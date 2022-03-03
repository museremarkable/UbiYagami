
CXX = g++
HDF5 = /opt/anaconda3/bin/h5c++

all: struct-read hdf5-read

struct-read: struct-read.cpp
	$(CXX) -o $@ $^

hdf5-read: hdf5-read.cpp
	$(HDF5) -o $@ $^

clean:
	rm -f *.o struct-read hdf5-read
