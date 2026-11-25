#ifndef EBOOK_MOBILE_ORT_PROBE_H
#define EBOOK_MOBILE_ORT_PROBE_H
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif

// Strings returned here use malloc; the caller releases them with FreeString.
char *MobileOrtProvidersJSON(void);
void MobileOrtFreeString(char *value);

// Backend-only proof. Text-to-phoneme IDs are prepared separately and labelled.
void *MobileOrtCreateSuxin(const char *model_path, int threads,
                         double *initialization_seconds, char **error);
int MobileOrtRunSuxin(void *handle, const int64_t *ids, size_t id_count,
                     float **samples, size_t *sample_count,
                     double *generation_seconds, char **error);
void MobileOrtFreeSamples(float *samples);
void MobileOrtDestroySuxin(void *handle);

#ifdef __cplusplus
}
#endif
#endif
