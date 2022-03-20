import struct

def read_answer_from_file(data_file_path):
    struct_fmt = '=iiidi' # 
    struct_len = struct.calcsize(struct_fmt)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    results = []
    with open(data_file_path, "rb") as f:
        while True:
            data = f.read(struct_len)
            if not data: break
            s = struct_unpack(data)
            results.append(s)
    return results

def read_binary_mit_pointer(data_file_path, start, length): #read 100 lines from starting point
    struct_fmt = '=iiidi' #
    struct_len = struct.calcsize(struct_fmt)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    results = []
    starting_byte = start * struct_len
    with open(data_file_path, "rb") as f:
        f.seek(starting_byte)
        for i in range(length):
            data = f.read(struct_len)
            if not data:
                break
            s = struct_unpack(data)
            results.append(s)
    return results

path_result = "results/trader1"
path_true = "data_test/100x1000x1000"
for ix in range(1,11):
	data_file_path = path_result + '/' + 'trade' + str(ix)
	answer_file_path = path_true + '/' + 'trade' + str(ix)
	results_g = read_answer_from_file(data_file_path)
	results_a = read_binary_mit_pointer(data_file_path, 0, len(results_g))
	print(f"Result length {len(results_g)} ")
	# print(f"True length {len(results_a)}")
	rang = min(len(results_g), len(results_a))
	diff = [ (x,y) for x, y in zip(results_a, results_g) if x!=y]
	if len(diff) == 0:
		print(f"trade{ix} correct")
	else:
		print(f"trade{ix} has diff")
		with open(path_result + f"/diff{ix}", "w") as f:
			f.write(f"{diff}")
print("done")