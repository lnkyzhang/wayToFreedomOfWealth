import os


def delete_num(srcpath, outpath):
    filelist = os.listdir(srcpath)
    os.makedirs(outpath)

    for file in filelist:
        f = open(srcpath + r"\\" + file, 'r', encoding='UTF-8')

        src_name = file.split('.')[0]
        dst_name = src_name + '.txt'

        outfile = open(outpath + '/' + dst_name, 'w')

        for line in f.readlines():
            line = line[:18] + line[23:]
            line = line.rstrip()
            outfile.write(line + '\n')

    f.close()
    outfile.close()


if __name__ == '__main__':
    delete_num(r'C:\Users\DuoWei\Desktop\locksteplog', r'E:\labelTxt')
