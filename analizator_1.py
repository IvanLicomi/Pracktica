from DBcm import UseDatabase, ConnectError, CredentialsError, SQLError
from collections import OrderedDict
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
        inputData[0]['distance'],
        inputData[0]['lr'][1],
        inputData[0]['rr'][1],
    ], ]
    x1, x2 = 0, 0
    temp = 0  # Для накапления длинны между точками

    tempList = []
    ly1 = inputData[0]['lr'][1]
    ly2 = inputData[1]['lr'][1]
    ry1 = inputData[0]['rr'][1]
    ry2 = inputData[1]['rr'][1]
    speed = inputData[1]['speed']
    dTime = (inputData[1]['time'] - inputData[0]['time']).total_seconds()
    

    x2 += speed * dTime
    tempList = []
    tempList.append(x2)
    tempList.append(ly1)
    tempList.append(ry2)
    greenPoint.append(tempList)

    for i in range(1, len(inputData)):
        tempList = []
        ly1 = inputData[i-1]['lr'][1]
        ly2 = inputData[i]['lr'][1]
        ry1 = inputData[i-1]['rr'][1]
        ry2 = inputData[i]['rr'][1]
        speed = inputData[i]['speed']
        dTime = (inputData[i]['time'] - 
                 inputData[i-1]['time']).total_seconds()

        if speed == 0:  # Остановка
            continue
        else:
            # print(inputData[1][i-1])
            x1 = x2  # Запоминание предыдущего значение
            x2 += speed * dTime
            temp += x2 - x1  # Накопление длинны между точками
            if temp >= lenghtSegment:
                for _ in range(int(temp//lenghtSegment)):
                    ly = ly1 + ((ly2 - ly1) *
                                (lenghtSegment * len(greenPoint) - x1))/(x2-x1)
                    ry = ry1 + ((ry2 - ry1) *
                                (lenghtSegment * len(greenPoint) - x1))/(x2-x1)
                    tempList = []
                    tempList.append(lenghtSegment * len(greenPoint))
                    tempList.append(ly)
                    tempList.append(ry)
                    # print(tempList)
                    greenPoint.append(tempList)
                    temp -= lenghtSegment
            else:
                continue
    
    ly = ly1 + ((ly2 - ly1) *
                (inputData[-1]['distance'] - x1))/(x2-x1)
    ry = ry1 + ((ry2 - ry1) *
                (inputData[-1]['distance'] - x1))/(x2-x1)
    tempList = []
    tempList.append(inputData[-1]['distance'])
    tempList.append(ly)
    tempList.append(ry)
    greenPoint.append(tempList)
    temp -= lenghtSegment

    return greenPoint


def callback(Data, body) -> 'dict':
    dictList = eval(body)

    for cadr in dictList.keys():
        dictList[cadr]['time'] = datetime.strptime(
            dictList[cadr]['time'], "%Y-%m-%d %H:%M:%S.%f")
        Data.append(dictList[cadr])

    # Расчет растояния
    distance = 0
    Data[0]['distance'] = distance

    for i in range(1, len(Data)):
        dTime = (Data[i]['time'] - Data[i-1]['time']).total_seconds()
        Data[i]['distance'] = distance + Data[i]['speed'] * dTime
        distance += Data[i]['speed'] * dTime


def sow_conv(listCadr: list, listGreenPoint: list) -> None:
    listX = []
    for cadr in listCadr:
        listX.append(cadr['distance'])

    listLY = []
    for cadr in listCadr:
        listLY.append(cadr['lr'][1])

    listRY = []
    for cadr in listCadr:
        listRY.append(cadr['wc'][1] - cadr['rr'][1])

    greenlistX = [i[0] for i in listGreenPoint]
    greenlistLeftY = [i[1] for i in listGreenPoint]

    plt.plot(listLY, listX, listRY, listX)            # построение графика
    plt.plot(greenlistLeftY, greenlistX)
    plt.show()


with open("data.json", "r") as read_file:
    callback(testInputData, read_file.read())
    ls = int(input("Длинна сегмента:"))
    sow_conv(testInputData, searh_point(testInputData, ls))
