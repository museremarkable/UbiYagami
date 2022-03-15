import numpy as np
import h5py

class DataReader:
    """
    read order from file, send order to exchange, (receive result from  exchanger? is it essential?)
    """
    def __init__(self, client_id, data_file_path, res_file_path):

        self.trade_list = [[]] * 10
        # client_id used to identify different client server
        self.client_id = client_id
        self.all_page = [] 
        self.data_file_path = data_file_path
        self.res_file_path = res_file_path
        self.hook_mtx = h5py.File(data_file_path + '/' + "hook.h5", 'r')['hook']
        self.hook_position = [0] * 10
    
    # process all data, alter that then trans these data
    def data_read(self):
        """
        read all data from file
        """
        order_id_path = self.data_file_path +'/'+ "order_id" + str(self.client_id) + ".h5"
        direction_path = self.data_file_path + '/'+ "direction" + str(self.client_id) + ".h5"
        price_path = self.data_file_path + '/'+ "price" + str(self.client_id) + ".h5"
        volume_path = self.data_file_path + '/'+ "volume" + str(self.client_id) + ".h5"
        type_path = self.data_file_path + '/'+ "type" + str(self.client_id) + ".h5"

        order_id_mtx = h5py.File(order_id_path, 'r')['order_id']
        direction_mtx = h5py.File(direction_path, 'r')['direction']
        price_mtx = h5py.File(price_path, 'r')['price']
        volume_mtx = h5py.File(volume_path, 'r')['volume']
        type_mtx = h5py.File(type_path, 'r')['type']
        

        data_page_number = order_id_mtx.shape[0]
        data_row_number = order_id_mtx.shape[1]
        data_column_number = order_id_mtx.shape[2]        
        per_stock_page_number = int(data_page_number / 10)
        #data transform
        #this implementation only works for small data(100x10x10 0.06 per stock 100x100x100 35s per stock, 100x1000x1000 1240s per stock, it's unaccecptable)
        for curr_stock_id in range(10):
            #print(curr_stock_id)
            curr_order_id_page = order_id_mtx[curr_stock_id].reshape(-1)
            curr_direction_page = direction_mtx[curr_stock_id].reshape(-1)
            curr_price_page = price_mtx[curr_stock_id].reshape(-1)
            curr_volumn_page = volume_mtx[curr_stock_id].reshape(-1)
            curr_type_page = type_mtx[curr_stock_id].reshape(-1)
            for i in range(1, per_stock_page_number):
                temp_order_id_page = order_id_mtx[i * 10 + curr_stock_id].reshape(-1)
                temp_direction_page = direction_mtx[i * 10 + curr_stock_id].reshape(-1)
                temp_price_page = price_mtx[i * 10 + curr_stock_id].reshape(-1)
                temp_volume_page = volume_mtx[i * 10 + curr_stock_id].reshape(-1)
                temp_type_page = type_mtx[i * 10 + curr_stock_id].reshape(-1)
                curr_order_id_page = np.concatenate((curr_order_id_page,temp_order_id_page))
                curr_direction_page = np.concatenate((curr_direction_page, temp_direction_page))
                curr_price_page = np.concatenate((curr_price_page, temp_price_page))
                curr_volumn_page = np.concatenate((curr_volumn_page, temp_volume_page))
                curr_type_page = np.concatenate((curr_type_page, temp_type_page))
                # time_end=time.time()         
                # print('totally cost',time_end-time_start)
            #convert 2d matrix data to 1d array
            # curr_order_id_page = curr_order_id_page.flatten()
            # curr_direction_page = curr_direction_page.flatten()
            # curr_price_page = curr_price_page.flatten()
            # curr_volumn_page = curr_volumn_page.flatten()
            # curr_type_page = curr_type_page.flatten()
            # curr_order_page is a 2d matrix (5000x5), coresponding order_id, direction, price, volumn, type corresponding one stock
            curr_order_page = np.transpose([curr_order_id_page, curr_direction_page, curr_price_page, curr_volumn_page, curr_type_page])
            # sort curr_order_page by order_id
            curr_order_page = curr_order_page[curr_order_page[:, 0].argsort()] 
            self.all_page.append(curr_order_page)
       