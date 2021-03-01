from DBcm import UseDatabase, ConnectError, CredentialsError, SQLError
from random import randint
from pprint import pprint
from datetime import datetime
import matplotlib.pyplot as plt
import pika
import sys
import os


DBCONFIG = {'host': '192.168.1.254',
            'user': 'user2',
            'password': '0011',
            'database': 'videoai', }

testInputData = list()


def loadDataBase(inputData: list, CurrentData: list) -> 'list':
    """Отправляет данные в БД, если в данных есть отличия."""
    if inputData != CurrentData:
        try:
            with UseDatabase(DBCONFIG) as cursor:
                _SQl = """INSERT INTO lenta_conv(comment)
                        VALUES ('Обнаружены изенения')"""
                cursor.execute(
                    _SQl)  # 'Обнаружены изенения в {0} сегменте'.format(segmentCurrent))
                # for row in inputData:
                #     _SQl = """INSERT INTO lenta_segment(query, width, left_side, right_side)
                #             VALUES(%s, %s, %s, %s,)"""
                #     cursor.execute(_SQl, row)
            return inputData

        except ConnectError as err:
            print('Is your database switched on? Error: ', str(err))
        except CredentialsError as err:
            print('User-id/Password issues. Error: ', str(err))
        except SQLError as err:
            print('Is your query correct? Error: ', str(err))
        except Exception as err:
            print('Somthing went wrong: ', str(err))
        return 'Error'
    else:
        return CurrentData


def searh_point(inputData: list, lenghtSegment: int) -> 'list':
    """Создает копию конвейера, разбивая введеные данны(inputData) на сегменты длинной(lenghtSegment)."""
    greenPoint = [[
        (inputData[0][3], inputData[0][1]),
        (inputData[0][3], inputData[1][0] + inputData[1][1])
    ], ]
    print(greenPoint)
    x1, x2 = 0, 0
    temp = 0  # Для накапления длинны между точками

    for i in range(1, len(inputData)):
        tempList = []
        ly1 = inputData[i-1][1]
        ly2, ry2, s2 = inputData[i][1:4]
        dTime = abs((inputData[i][4] - inputData[i-1][4]).total_seconds())

        if s2 == 0:  # Остановка
            continue
        else:
            x1 = x2  # Запоминание предыдущего значение
            x2 += s2 * dTime
            temp += x2 - x1  # Накопление длинны между точками
            if temp >= lenghtSegment:
                for _ in range(int(temp//lenghtSegment)):
                    y = ly1 + ((ly2 - ly1) *
                               (lenghtSegment * len(greenPoint) - x1))/(x2-x1)
                    tempList = []
                    tempList.append((lenghtSegment * len(greenPoint), y))
                    tempList.append(
                        (lenghtSegment * len(greenPoint), y + inputData[i][0]))
                    greenPoint.append(tempList)
                    temp -= lenghtSegment
            else:
                continue
    return greenPoint


def parse_json(body) -> 'list':
    data = eval(body)
    print(data)
    for i in data:
        tempList = list()
        tempList.append(data[i]['wc'][1])  # Ширина ленты
        tempList.append(data[i]['lr'][1])  # Ширина левого ролика
        tempList.append(data[i]['rr'][1])  # Ширина правого ролика
        tempList.append(4)  # Скорость. Временно!
        tempList.append(datetime.strptime(
            data[i]['time'], "%Y-%m-%d %H:%M:%S.%f"))  # Время
        tempList.append(data[i]['joint'])  # Стык
        if data[i]['joint'] == True:
            tempList.append(data[i]['ljoint'])
        testInputData.append(tempList)
    print(testInputData)


def callback(inputData) -> 'dict':
    joint = False
    listSegment = dict()
    for data in inputData:
        print(data)
        if data[5] == True and joint == False:
            print('Обнаружен новый стык!')
            joint = True
        elif data[5] == True and joint == True:
            print('Стык повторился!')
            joint = True
        else:
            print('Построение отрезка!')
            joint = False

    # list_x = [0]
    # for i in range(1, len(testInputData)):
    #     dTime = (testInputData[i][4] - testInputData[i-1][4]).total_seconds()
    #     list_x.append(list_x[i-1] + testInputData[i][3]*abs(dTime))

    # segmentList = searh_point(testInputData, 50) # Получаем копию конвейера, разбитого на сегменты

    # left_list_Y = [i[1] for i in testInputData]
    # right_list_Y = [i[0] + i[1] for i in testInputData]

    # green_list_x = [i[0][0] for i in segmentList]
    # green_left_list_Y = [i[0][1] for i in segmentList]
    # green_right_list_Y = [i[1][1] for i in segmentList]

    # print("Длина ", list_x[-1])
    # print(abs(yf))
    # print("Длина ", list_x[-1])
    # print("Длина ленты примерно ", lenghtSegment * int(max(yf))/10000)

    # print()
    # L = np.array(green_left_list_Y)
    # L = np.round(L, 1)
    # L -= np.mean(L)
    # L *= scipy.signal.windows.hann(len(L))
    # fft = np.fft.rfft(L, norm="ortho")
    # plt.show()

    # plt.subplot(2, 1, 1)
    # plt.plot(left_list_Y, list_x, right_list_Y, list_x, green_left_list_Y, green_list_x)              # построение графика
    # plt.title("Сравнение") # заголовок
    # plt.ylabel("Синие точки", fontsize=14) # ось ординат
    # plt.grid(True) # включение отображение сетки
    # # Временно!
    # plt.subplot(2, 1, 2)
    # plt.plot(green_left_list_Y, green_list_x, green_right_list_Y, green_list_x)               # построение графика
    # plt.xlabel("x", fontsize=14)  # ось абсцисс
    # plt.ylabel("Зеленые точки", fontsize=14) # ось ординат
    # plt.grid(True)

    # # Временно!
    # plt.plot(abs(fft)) # построение графика
    # plt.xlabel("x", fontsize=14)  # ось абсцисс
    # plt.ylabel("Фурье", fontsize=14) # ось ординат
    # plt.grid(True)
    # plt.show()


with open("data.json", "r") as read_file:
    parse_json(read_file.read())
    callback(testInputData)
