./waf --run "xiaoke --duration=1 --seed=3 --producerNum=2 --consumerClass=ConsumerZipfMandelbrot">output/out.log 2>&1
cd script
python cmp.py |wc
cd ..
