import struct
from argparse import ArgumentParser
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
parser = ArgumentParser()
parser.add_argument("-g", "--generated",  help="generated answer")
parser.add_argument("-a", "--answer",  help="correct answer")
args = parser.parse_args()
total_wrong_number = 0
total_number = 0
for i in range(10):
    print("======================================================================")
    print("testing stock %d result" % (i + 1))
    data_file_path = args.generated + '/' + 'trade' + str(i + 1)
    answer_file_path = args.answer + '/' + 'trade' + str(i + 1)
    results_g = read_answer_from_file(data_file_path)
    results_a = read_answer_from_file(answer_file_path)
    if len(results_a) != len(results_g):
        print("stock %d 's result length is not correct" % (i + 1))
        print("our answer length is %d" % (len(results_g)))
        print("correct answer length is %d" % (len(results_a)))
    else:
        current_total_number = 0
        current_wrong_number = 0
        print("stock %d length test pass" % (i + 1))
        total_number += len(results_g)
        current_total_number = len(results_g)
        for x, y in zip(results_a, results_g):
            index = 1
            if x != y:
                current_wrong_number += 1
                print("---------WRONG ANSWER IN STOCK %d LINE %d --------" % (i, index))
                index += 1
                print(f"our answer is: %s, while correct is: %s" % (x,y))
        total_wrong_number += current_wrong_number
        current_ratio = (current_total_number - current_wrong_number) / current_total_number
        print("stock %d 's correct ratio is %d percent" % (i+1, current_ratio*100))
print("=======================RESULT COMPARE COMPLETE=================================")
correct_ratio = (total_number - total_wrong_number) / total_number
print("total correct ratio is %d percent" % (correct_ratio * 100))


