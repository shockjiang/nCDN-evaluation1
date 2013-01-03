#coding=utf-8

#usage:
#cmd e.g: 
#by Shock Jiang, 2012.



#coding=utf-8

#usage:
#cmd e.g: ./FILENAME.sh
#by Shock Jiang, 2012.



sudo aptitude install libboost-all-dev -y
sudo apt-get install python-dev python-pygraphviz python-kiwi -y
sudo apt-get install python-pygoocanvas python-gnome2 -y
sudo apt-get install python-gnomedesktop python-rsvg ipython -y

if [ ! -d "ndnSIM"]; then 
    mkdir "ndnSIM" 
fi
cd ndnSIM
git clone git://github.com/cawka/ns-3-dev-ndnSIM.git ns-3
git clone git://github.com/cawka/pybindgen.git pybindgen

git clone https://github.com/shockjiang/ndnSIM.git ns-3/src/ndnSIM
git clone https://github.com/shockjiang/paperHelper.git ns-3/shock


cd ns-3
./waf configure --enable-examples
./waf

