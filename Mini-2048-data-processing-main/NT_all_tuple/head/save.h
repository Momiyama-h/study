#include <zlib.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace NT1 {
void writeEvs(FILE*);
}
namespace NT2 {
void writeEvs(FILE*);
}
namespace NT3 {
void writeEvs(FILE*);
}
namespace NT4 {
void writeEvs(FILE*);
}
namespace NT5 {
void writeEvs(FILE*);
}
namespace NT6 {
void writeEvs(FILE*);
}
namespace NT7 {
void writeEvs(FILE*);
}
namespace NT8 {
void writeEvs(FILE*);
}
namespace NT9 {
void writeEvs(FILE*);
}

extern const long long STORAGE_COUNT;
extern const int nt;

void saveEvs(int seed, int TupleNumber, int storage_c) {
  char filename[1024];
  snprintf(filename, sizeof(filename),
           "../dat/%dtuple_data_TupleNumber%d_seed%d_storage_c%d.dat.zip", nt,
           TupleNumber, seed, storage_c);

  // 一時ファイルにデータを書き出し
  FILE* temp_fp = tmpfile();
  if (!temp_fp) {
    fprintf(stderr, "Temporary file creation failed.\n");
    return;
  }

  // デバッグ情報：書き込み前のファイルサイズを確認
  printf("Debug: Writing data for N-tuple %d\n", nt);

  // N-tupleに応じたwriteEvs関数を呼び出し
  switch (nt) {
    case 1:
      printf("Debug: Starting NT1::writeEvs\n");
      NT1::writeEvs(temp_fp);
      printf("Debug: Completed NT1::writeEvs\n");
      break;
    case 2:
      printf("Debug: Starting NT2::writeEvs\n");
      NT2::writeEvs(temp_fp);
      printf("Debug: Completed NT2::writeEvs\n");
      break;
    case 3:
      printf("Debug: Starting NT3::writeEvs\n");
      NT3::writeEvs(temp_fp);
      printf("Debug: Completed NT3::writeEvs\n");
      break;
    case 4:
      printf("Debug: Starting NT4::writeEvs\n");
      NT4::writeEvs(temp_fp);
      printf("Debug: Completed NT4::writeEvs\n");
      break;
    case 5:
      printf("Debug: Starting NT5::writeEvs\n");
      NT5::writeEvs(temp_fp);
      printf("Debug: Completed NT5::writeEvs\n");
      break;
    case 6:
      printf("Debug: Starting NT6::writeEvs\n");
      NT6::writeEvs(temp_fp);
      printf("Debug: Completed NT6::writeEvs\n");
      break;
    case 7:
      printf("Debug: Starting NT7::writeEvs\n");
      NT7::writeEvs(temp_fp);
      printf("Debug: Completed NT7::writeEvs\n");
      break;
    case 8:
      printf("Debug: Starting NT8::writeEvs\n");
      NT8::writeEvs(temp_fp);
      printf("Debug: Completed NT8::writeEvs\n");
      break;
    case 9:
      printf("Debug: Starting NT9::writeEvs\n");
      NT9::writeEvs(temp_fp);
      printf("Debug: Completed NT9::writeEvs\n");
      break;
    default:
      printf("Debug: Starting NT1::writeEvs\n");
      NT1::writeEvs(temp_fp);
      printf("Debug: Completed NT1::writeEvs\n");
      break;
  }

  // デバッグ情報：ファイルサイズを確認
  fseek(temp_fp, 0L, SEEK_END);
  long file_size = ftell(temp_fp);
  rewind(temp_fp);
  printf("Debug: Temporary file size before compression: %ld bytes\n", file_size);
  printf("Debug: Expected element size: %ld elements\n", 29282L);
  printf("Debug: Expected file size (elements * sizeof(int)): %ld bytes\n", 29282L * sizeof(int));
  printf("Debug: Actual/Expected ratio: %.2f%%\n", (file_size * 100.0) / (29282L * sizeof(int)));

  // ZIP圧縮用のファイルを開く
  printf("Debug: Opening ZIP file: %s\n", filename);
  gzFile zip_fp = gzopen(filename, "wb");
  if (!zip_fp) {
    fprintf(stderr, "Could not open zip file for writing.\n");
    fclose(temp_fp);
    return;
  }

  // バッファを使用してデータを圧縮
  printf("Debug: Starting compression process\n");
  unsigned char buffer[4096];
  size_t bytes_read;
  size_t total_bytes_written = 0;
  size_t compression_chunks = 0;
  
  while ((bytes_read = fread(buffer, 1, sizeof(buffer), temp_fp)) > 0) {
    compression_chunks++;
    printf("Debug: Processing chunk %zu, read %zu bytes\n", compression_chunks, bytes_read);
    size_t written = gzwrite(zip_fp, buffer, bytes_read);
    if (written != bytes_read) {
      fprintf(stderr, "Error writing to zip file. Expected %zu bytes, wrote %zu bytes.\n", 
              bytes_read, written);
      fclose(temp_fp);
      gzclose(zip_fp);
      return;
    }
    total_bytes_written += written;
  }

  printf("Debug: Compression complete:\n");
  printf("Debug: - Total chunks processed: %zu\n", compression_chunks);
  printf("Debug: - Total bytes written: %zu\n", total_bytes_written);
  printf("Debug: - Compression ratio: %.2f%%\n", (total_bytes_written * 100.0) / file_size);

  // ファイルを閉じる
  fclose(temp_fp);
  gzclose(zip_fp);

  printf("Stored (ZIP) %s\n", filename);

  storage_c++;
  if (storage_c == STORAGE_COUNT) exit(0);
}