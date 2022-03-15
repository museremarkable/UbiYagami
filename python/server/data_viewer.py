from data_type import *
import h5py

class data_viewer:
	def __init__(self, base_path="data_test/100x10x10/"):
		order_id_path = base_path + "order_id1.h5"
		direction_path = base_path + "direction1.h5"
		price_path = base_path + "price1.h5"
		volume_path = base_path + "volume1.h5"
		type_path = base_path + "type1.h5"

		self.order_id_mtx = h5py.File(order_id_path, 'r')['order_id']
		self.direction_mtx = h5py.File(direction_path, 'r')['direction']
		self.price_mtx = h5py.File(price_path, 'r')['price']
		self.volume_mtx = h5py.File(volume_path, 'r')['volume']
		self.type_mtx = h5py.File(type_path, 'r')['type']

	def get_order_at(self, x, y, z):
		print(f" Stock code: {x%10+1}")
		print(f" Order ID: {self.order_id_mtx[x,y,z]}")
		print(f" Direction: {self.direction_mtx[x,y,z]}")
		print(f" Price: {self.price_mtx[x,y,z]}")
		print(f" Volume: {self.volume_mtx[x,y,z]}")
		print(f" Type: {self.type_mtx[x,y,z]}")

		return Order(x%10 + 1,
					self.order_id_mtx[x,y,z],
					DirectionType(self.direction_mtx[x,y,z]),
					self.price_mtx[x,y,z],
					self.volume_mtx[x,y,z],
					OrderType(self.type_mtx[x,y,z]))


# v = data_viewer()
# v.get_order_at(0,0,1)