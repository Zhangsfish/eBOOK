#include "SuxinBridge.h"
#include <onnxruntime/onnxruntime_cxx_api.h>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <vector>
#include <sys/resource.h>

namespace {
using Clock = std::chrono::steady_clock;
char *Copy(const char *message) {
  const size_t length = std::strlen(message);
  auto *copy = static_cast<char *>(std::malloc(length + 1));
  if (copy) std::memcpy(copy, message, length + 1);
  return copy;
}
struct Engine {
  Ort::Env env{ORT_LOGGING_LEVEL_ERROR, "eBOOK-local-Suxin"};
  Ort::SessionOptions options;
  std::unique_ptr<Ort::Session> session;
  std::mutex mutex;
  std::shared_ptr<Ort::RunOptions> running;
  Engine(const char *path, int threads) {
    options.SetIntraOpNumThreads(threads);
    options.SetInterOpNumThreads(1);
    options.SetExecutionMode(ORT_SEQUENTIAL);
    options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
    session = std::make_unique<Ort::Session>(env, path, options);
    Ort::AllocatorWithDefaultOptions allocator;
    const char *names[] = {"input", "input_lengths", "scales"};
    if (session->GetInputCount() != 3 || session->GetOutputCount() != 1)
      throw std::runtime_error("Unexpected Suxin interface");
    for (size_t i = 0; i < 3; ++i) {
      auto actual = session->GetInputNameAllocated(i, allocator);
      if (std::string(actual.get()) != names[i]) throw std::runtime_error("Unexpected Suxin input");
    }
  }
};
}

void *EBookSuxinCreate(const char *path, int threads, double *seconds, char **error) {
  try {
    if (!path || !seconds || !error || threads < 1 || threads > 4)
      throw std::runtime_error("Invalid model request");
    *error = nullptr;
    const auto start = Clock::now();
    auto engine = std::make_unique<Engine>(path, threads);
    *seconds = std::chrono::duration<double>(Clock::now() - start).count();
    return engine.release();
  } catch (const std::exception &problem) {
    if (error) *error = Copy(problem.what());
    return nullptr;
  }
}

int EBookSuxinRun(void *handle, const int64_t *ids, size_t count, float speed,
                 float **samples, size_t *frames, double *seconds, char **error) {
  Engine *engine = static_cast<Engine *>(handle);
  try {
    if (!engine || !ids || !count || count > 512 || !std::isfinite(speed) ||
        speed < .5f || speed > 2.f || !samples || !frames || !seconds || !error)
      throw std::runtime_error("Invalid bounded synthesis request");
    *samples = nullptr; *frames = 0; *error = nullptr;
    auto run = std::make_shared<Ort::RunOptions>();
    {
      std::lock_guard<std::mutex> lock(engine->mutex);
      engine->running = run;
    }
    std::vector<int64_t> input(ids, ids + count);
    int64_t shape[] = {1, static_cast<int64_t>(count)}, length = static_cast<int64_t>(count), lengthShape[] = {1};
    float scales[] = {0.f, 1.f / speed, 0.f};
    int64_t scaleShape[] = {3};
    auto memory = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
    std::vector<Ort::Value> values;
    values.emplace_back(Ort::Value::CreateTensor<int64_t>(memory, input.data(), input.size(), shape, 2));
    values.emplace_back(Ort::Value::CreateTensor<int64_t>(memory, &length, 1, lengthShape, 1));
    values.emplace_back(Ort::Value::CreateTensor<float>(memory, scales, 3, scaleShape, 1));
    const char *names[] = {"input", "input_lengths", "scales"};
    Ort::AllocatorWithDefaultOptions allocator;
    auto outputName = engine->session->GetOutputNameAllocated(0, allocator);
    const char *outputs[] = {outputName.get()};
    const auto start = Clock::now();
    auto result = engine->session->Run(*run, names, values.data(), 3, outputs, 1);
    *seconds = std::chrono::duration<double>(Clock::now() - start).count();
    const auto info = result[0].GetTensorTypeAndShapeInfo();
    const size_t size = info.GetElementCount();
    if (info.GetElementType() != ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT || !size || size > 22050 * 30)
      throw std::runtime_error("Invalid bounded waveform");
    const float *audio = result[0].GetTensorData<float>();
    double energy = 0;
    for (size_t i = 0; i < size; ++i) {
      if (!std::isfinite(audio[i])) throw std::runtime_error("Nonfinite waveform");
      energy += audio[i] * audio[i];
    }
    if (std::sqrt(energy / size) < .001) throw std::runtime_error("Silent waveform");
    auto *copy = static_cast<float *>(std::malloc(size * sizeof(float)));
    if (!copy) throw std::bad_alloc();
    std::memcpy(copy, audio, size * sizeof(float));
    *samples = copy; *frames = size;
    {
      std::lock_guard<std::mutex> lock(engine->mutex);
      engine->running.reset();
    }
    return 1;
  } catch (const std::exception &problem) {
    if (engine) { std::lock_guard<std::mutex> lock(engine->mutex); engine->running.reset(); }
    if (error) *error = Copy(problem.what());
    return 0;
  }
}

void EBookSuxinCancel(void *handle) {
  if (!handle) return;
  auto *engine = static_cast<Engine *>(handle);
  std::shared_ptr<Ort::RunOptions> running;
  { std::lock_guard<std::mutex> lock(engine->mutex); running = engine->running; }
  if (running) { try { running->SetTerminate(); } catch (...) {} }
}
void EBookSuxinDestroy(void *handle) { delete static_cast<Engine *>(handle); }
void EBookSuxinFree(void *memory) { std::free(memory); }
const char *EBookSuxinRuntimeVersion(void) { return OrtGetApiBase()->GetVersionString(); }
uint64_t EBookSuxinPeakResidentBytes(void) {
  rusage usage{};
  return getrusage(RUSAGE_SELF, &usage) == 0 ? static_cast<uint64_t>(usage.ru_maxrss) : 0;
}
