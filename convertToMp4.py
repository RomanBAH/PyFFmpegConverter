import os
import datetime
import time
import shutil
import glob

from tqdm import tqdm
from ffmpeg_progress_yield import FfmpegProgress
from videoprops import get_video_properties

# Пути для поиска файлов к конвертированию
srcList = [
    '../Video_01',
    '../Video_02',
]

# Список обрабатываемых расширений
extList = ['.avi', '.mp4', '.mkv', '.mpeg', '.wmv', '.flv', '.m4v']

# По умолчанию (False) новый файл сразу пишется в ту же директорию где лежит исходный, только в случае совпадения имён
# переменная переопределяется в скрипте, тогда новый файл сначала пишется в папку tmp, потом перемещается и заменяет
# исходный. Но можно принудительно задать всегда использовать папку tmp утсановив True.
useTmpfolder = False


# Функция непосредственной конвертации
def convert_to_mp4(input_file, output_file, inputprops, useTmpfolder):
    output_file_orig = output_file
    video_bitrate = 2000000
    input_bitrate = int(inputprops['bit_rate'])
    tmp_path = ''

    # Если битред исходника меньше базового в переменной, то используем его, избегая бессмысленного увеличения файла
    if input_bitrate < video_bitrate:
        video_bitrate = input_bitrate

    start_time = time.time()

    # Если отмечено для использования временной папки, перенапнравляем пути
    if useTmpfolder:
        fullfilename = os.path.basename(input_file)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        tmp_path = dir_path + '\\tmp\\' + fullfilename
        output_file = tmp_path

        # Зачистка директории tmp
        files = glob.glob(dir_path + '\\tmp\\*')
        for f in files:
            os.remove(f)

    # Непосредственная конвертация с выводом статус бара
    print("Start encode to HEVC with brate: %s k" % round(int(video_bitrate) / 1000))
    cmd = ['ffmpeg', '-i', input_file, '-ac', '2', '-b:a', str(video_bitrate), '-b:v', '2000000', '-c:a', 'aac', '-c:v',
           'libx265', output_file, '-y']
    ff = FfmpegProgress(cmd)
    with tqdm(total=100, desc="[Progress]") as pbar:
        for progress in ff.run_command_with_progress():
            pbar.update(progress - pbar.n)
        pbar.close()

    # Если отмечено использования временной папки, после конвертации выполняем перемещение выходного файла
    if useTmpfolder and tmp_path != '':
        shutil.move(tmp_path, output_file_orig)
        output_file = output_file_orig

    # Если файл найден, пишем ок, если нет, пишем ошибку
    if os.path.isfile(output_file):
        print('Finished')
        logtofile('Convert is ok, from ' + input_file + ' to ' + output_file)

        # Удаляем только если ранее не передан флаг использовать временную папку
        if not useTmpfolder:
            os.remove(input_file)
            print(input_file + ' was remoived')
            logtofile(input_file + ' was remoived')
    else:
        logtofile('Error convert with file ' + input_file)
        print('Error')

    # Вывод отчёта о времени
    print("Operation time %s minutes" % round((time.time() - start_time) / 60, 2))
    logtofile("Operation time %s minutes" % round((time.time() - start_time) / 60, 2))


# Функция логирования
def logtofile(message):
    now = datetime.datetime.now()
    date_time_str = now.strftime("%d.%m.%Y %H:%M:%S")

    f = open('log.txt', 'a', encoding="utf-8")
    f.write(date_time_str + ': ' + message + '\n')
    f.close()


# Проход по всем элементам srcList
for src in srcList:

    # Чтение папки
    for root, dirs, filenames in os.walk(src, topdown=False):
        # Проход по полученным файлам
        for filename in filenames:

            logtofile('###### Start trying file ' + filename + ' ######')

            # Непосредственная попытка конвертирпования
            try:

                inputfile = os.path.join(root, filename)
                fname, fextension = os.path.splitext(filename)

                # Проверка расширения
                if fextension.lower() in extList:

                    inputprops = get_video_properties(inputfile)
                    inputprops['bit_rate'] = inputprops.get('bit_rate', '2000000')
                    filepathdir = os.path.dirname(inputfile)
                    filepathdirFinal = filepathdir + '\\' + fname + '.mp4'

                    # Действие только если определён кодек и кодек не hevc
                    if inputprops['codec_name'] != "" and inputprops['codec_name'] != 'hevc':
                        print('\n')
                        print('[FILE INPUT] ', inputfile)

                        # Если расширение mp4 и файл результат уже существует, значит мы не можем конвертировать в
                        # тот же каталог, ставим флаг использования временной директории
                        if fextension.lower() == '.mp4' and os.path.isfile(filepathdirFinal):
                            useTmpfolder = True

                        convert_to_mp4(inputfile, filepathdirFinal, inputprops, useTmpfolder)

                        print('---------------\n')

                    else:
                        print('[SKIP] ' + '(' + inputprops['codec_name'] + ') ' + inputfile)
                        logtofile('[SKIP] ' + '(' + inputprops['codec_name'] + ') ' + inputfile)

                else:
                    print('[SKIP] ' + '(' + fextension + ') ' + inputfile)
                    logtofile('[SKIP] ' + '(' + fextension + ') ' + inputfile)

            except:
                print('Error in Try')
                logtofile('Error in Try')

            logtofile('---------------\n')

# os.system("pause")
