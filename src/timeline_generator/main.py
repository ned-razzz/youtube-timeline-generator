def main():
  
      # 각 노래 시작점 탐지
      print()
      print("노래 검색 시작...")
      detect_results = detect_timeline(long_audio, 
                                      fingerprints, 
                                      window_size, 
                                      hop_size,
                                      sample_rate, 
                                      similarity_threshold)
      print("\n검색 완료")


if __name__ == "__main__":
    main()