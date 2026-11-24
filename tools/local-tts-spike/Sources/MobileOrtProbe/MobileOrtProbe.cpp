#include "MobileOrtProbe.h"
#include <onnxruntime/onnxruntime_cxx_api.h>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using Clock = std::chrono::steady_clock;
double Seconds(Clock::time_point start) {
  return std::chrono::duration<double>(Clock::now() - start).count();
}
char *Copy(const std::string &value) {
  auto *result = static_cast<char *>(std::malloc(value.size() + 1));
  if (result) std::memcpy(result, value.c_str(), value.size() + 1);
  return result;
}
std::string Quote(const std::string &value) {
  std::string result = "\"";
  for (char ch : value) {
    if (ch == '\\' || ch == '"') result += '\\';
    if (static_cast<unsigned char>(ch) >= 32) result += ch;
  }
  return result + "\"";
}
struct SuxinSession {
  Ort::Env env{ORT_LOGGING_LEVEL_WARNING, "eBOOK-S02A2-backend-only"};
  Ort::SessionOptions options;
  std::unique_ptr<Ort::Session> session;
  SuxinSession(const char *path, int threads) {
    options.SetIntraOpNumThreads(threads);
    options.SetInterOpNumThreads(1);
    options.SetExecutionMode(ORT_SEQUENTIAL);
    options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
    session = std::make_unique<Ort::Session>(env, path, options);
    Ort::AllocatorWithDefaultOptions allocator;
    const char *expected[] = {"input", "input_lengths", "scales"};
    if (session->GetInputCount() != 3 || session->GetOutputCount() != 1)
      throw std::runtime_error("Unexpected Suxin graph interface");
    for (size_t i = 0; i < 3; ++i) {
      auto name = session->GetInputNameAllocated(i, allocator);
      if (std::string(name.get()) != expected[i])
        throw std::runtime_error("Unexpected Suxin input name/order");
    }
  }
};
}

char *MobileOrtProvidersJSON(void) {
  try {
    auto providers = Ort::GetAvailableProviders();
    std::string value = "{\"status\":\"RUNTIME_ENUMERATED\",\"ort_version\":";
    value += Quote(OrtGetApiBase()->GetVersionString());
    value += ",\"available_providers\":[";
    for (size_t i = 0; i < providers.size(); ++i) {
      if (i) value += ',';
      value += Quote(providers[i]);
    }
    return Copy(value + "]}");
  } catch (const std::exception &error) {
    return Copy("{\"status\":\"RUNTIME_ENUMERATION_FAILED\",\"error\":" + Quote(error.what()) + "}");
  }
}
void MobileOrtFreeString(char *value) { std::free(value); }

void *MobileOrtCreateSuxin(const char *model_path, int threads,
                         double *initialization_seconds, char **error) {
  try {
    if (!model_path || !initialization_seconds || !error || threads < 1 || threads > 4)
      throw std::runtime_error("Invalid bounded backend request");
    *error = nullptr;
    auto start = Clock::now();
    auto handle = std::make_unique<SuxinSession>(model_path, threads);
    *initialization_seconds = Seconds(start);
    return handle.release();
  } catch (const std::exception &problem) {
    if (error) *error = Copy(problem.what());
    return nullptr;
  }
}
int MobileOrtRunSuxin(void *handle, const int64_t *ids, size_t id_count,
                     float **samples, size_t *sample_count,
                     double *generation_seconds, char **error) {
  try {
    if (!handle || !ids || !id_count || id_count > 2048 || !samples ||
        !sample_count || !generation_seconds || !error)
      throw std::runtime_error("Invalid bounded Suxin input");
    *samples = nullptr; *sample_count = 0; *error = nullptr;
    auto &engine = *static_cast<SuxinSession *>(handle);
    std::vector<int64_t> input(ids, ids + id_count);
    int64_t input_shape[] = {1, static_cast<int64_t>(id_count)};
    int64_t length = static_cast<int64_t>(id_count), length_shape[] = {1};
    float scales[] = {0.f, 1.f, 0.f};
    int64_t scales_shape[] = {3};
    auto memory = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
    std::vector<Ort::Value> values;
    values.emplace_back(Ort::Value::CreateTensor<int64_t>(memory, input.data(), input.size(), input_shape, 2));
    values.emplace_back(Ort::Value::CreateTensor<int64_t>(memory, &length, 1, length_shape, 1));
    values.emplace_back(Ort::Value::CreateTensor<float>(memory, scales, 3, scales_shape, 1));
    const char *names[] = {"input", "input_lengths", "scales"};
    Ort::AllocatorWithDefaultOptions allocator;
    auto output_name = engine.session->GetOutputNameAllocated(0, allocator);
    const char *output_names[] = {output_name.get()};
    auto start = Clock::now();
    auto output = engine.session->Run(Ort::RunOptions{nullptr}, names, values.data(), 3, output_names, 1);
    *generation_seconds = Seconds(start);
    auto info = output[0].GetTensorTypeAndShapeInfo();
    if (info.GetElementType() != ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT)
      throw std::runtime_error("Unexpected waveform element type");
    size_t count = info.GetElementCount();
    if (!count || count > 22050 * 120) throw std::runtime_error("Unexpected waveform length");
    const auto *audio = output[0].GetTensorData<float>();
    for (size_t i = 0; i < count; ++i)
      if (!std::isfinite(audio[i])) throw std::runtime_error("Nonfinite model output");
    auto *copy = static_cast<float *>(std::malloc(count * sizeof(float)));
    if (!copy) throw std::bad_alloc();
    std::memcpy(copy, audio, count * sizeof(float));
    *samples = copy; *sample_count = count;
    return 1;
  } catch (const std::exception &problem) {
    if (error) *error = Copy(problem.what());
    return 0;
  }
}
void MobileOrtFreeSamples(float *samples) { std::free(samples); }
void MobileOrtDestroySuxin(void *handle) { delete static_cast<SuxinSession *>(handle); }
