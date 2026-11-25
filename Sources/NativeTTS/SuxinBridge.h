#pragma once
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
void *EBookSuxinCreate(const char *path, int threads, double *seconds, char **error);
int EBookSuxinRun(void *handle, const int64_t *ids, size_t count, float speed,
                 float **samples, size_t *frames, double *seconds, char **error);
void EBookSuxinCancel(void *handle);
void EBookSuxinDestroy(void *handle);
void EBookSuxinFree(void *memory);
const char *EBookSuxinRuntimeVersion(void);
uint64_t EBookSuxinPeakResidentBytes(void);
#ifdef __cplusplus
}
#endif
