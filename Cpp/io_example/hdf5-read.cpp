#include <iostream>
#include <cstring>

#include "H5Cpp.h"
using namespace H5;

const H5std_string FILE_NAME("/data/100x1000x1000/price1.h5");
const H5std_string DATASET_NAME("price");

const int NX_SUB = 3;
const int NY_SUB = 4;
const int NZ_SUB = 2; //read a 3x4x2 matrix

const int RANK_OUT = 3;

int main() {
    double *data_read = new double [500 *1000 * 1000];
    memset(data_read, 0, sizeof(double) * 500 * 1000 * 1000);
    H5File file(FILE_NAME, H5F_ACC_RDONLY);
    DataSet dataset = file.openDataSet(DATASET_NAME);

    DataSpace dataspace = dataset.getSpace();
    int rank = dataspace.getSimpleExtentNdims();

    hsize_t dims_out[3];
    dataspace.getSimpleExtentDims(dims_out, NULL);

    printf("rank %d, shape (%llu, %llu, %llu)\n", rank, dims_out[0], dims_out[1], dims_out[2]);

    hsize_t offset[3];
    hsize_t count[3];
    offset[0] = 0;
    offset[1] = 0;
    offset[2] = 0;
    count[0] = NX_SUB;
    count[1] = NY_SUB;
    count[2] = NZ_SUB;
    dataspace.selectHyperslab(H5S_SELECT_SET, count, offset); //select in file, this api can set api

    hsize_t dimsm[3];
    dimsm[0] = 500;
    dimsm[1] = 1000;
    dimsm[2] = 1000;
    DataSpace memspace(RANK_OUT, dimsm);

    hsize_t offset_out[3];
    hsize_t count_out[3];
    offset_out[0] = 0;
    offset_out[1] = 0;
    offset_out[2] = 0;
    count_out[0] = NX_SUB;
    count_out[1] = NY_SUB;
    count_out[2] = NZ_SUB;
    memspace.selectHyperslab(H5S_SELECT_SET, count_out, offset_out); // select in memory

    dataset.read(data_read, PredType::NATIVE_DOUBLE, memspace, dataspace);
    //read from file to memory, you can set offset in memory space

    for (int i = 0; i < 5; ++i) {
        for (int j = 0; j < 5; ++j) {
            std::cout << data_read[i * (1000 * 1000) + j * 1000 + 0] << " ";
        }
        std::cout << std::endl;
    }

    std::cout << std::endl;
    for (int i = 0; i < 5; ++i) {
        for (int j = 0; j < 5; ++j) {
            std::cout << data_read[i * (1000 * 1000) + j * 1000 + 1] << " ";
        }
        std::cout << std::endl;
    }

    std::cout << std::endl;
    for (int i = 0; i < 5; ++i) {
        for (int j = 0; j < 5; ++j) {
            std::cout << data_read[i * (1000 * 1000) + j * 1000 + 2] << " ";
        }
        std::cout << std::endl;
    }
    delete[] data_read;

    return 0;
}
