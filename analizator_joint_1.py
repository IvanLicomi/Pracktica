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

testInputData = OrderedDict()


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


def searh_point(inputData: dict, lenghtSegment: int) -> 'list':
    """Создает копию конвейера, разбивая введеные данны(inputData) на сегменты длинной(lenghtSegment)."""
    greenPoint = [[
        inputData[1][0]['distance'],
        inputData[1][0]['lr'][1],
        inputData[1][0]['rr'][1],
    ], ]
    x1, x2 = 0, 0
    temp = 0  # Для накапления длинны между точками

    for iSegment in inputData:
        for iCadr in range(1, len(inputData[iSegment])):
            tempList = []
            ly1 = inputData[iSegment][iCadr-1]['lr'][1]
            ly2 = inputData[iSegment][iCadr]['lr'][1]
            ry1 = inputData[iSegment][iCadr-1]['rr'][1]
            ry2 = inputData[iSegment][iCadr]['rr'][1]
            speed = inputData[iSegment][iCadr]['speed']
            dTime = (inputData[iSegment][iCadr]['time'] -
                     inputData[iSegment][iCadr-1]['time']).total_seconds()

            if speed == 0:  # Остановка
                continue
            else:
                x1 = x2  # Запоминание предыдущего значение
                x2 += speed * dTime
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
        # return greenPoint


def callback(body) -> 'dict':
    JOINT = False
    currentSegment = 0
    dictSegment = OrderedDict()
    testInputData.update(eval(body))

    for i in testInputData:
        if testInputData[i]['joint'] == True and JOINT == False:
            print('Обнаружен новый стык!')
            JOINT = True
            currentSegment += 1
            dictSegment[currentSegment] = []
            testInputData[i]['time'] = datetime.strptime(
                testInputData[i]['time'], "%Y-%m-%d %H:%M:%S.%f")
            dictSegment[currentSegment].append(testInputData[i])
        elif testInputData[i]['joint'] == True and JOINT == True:
            print('Стык повторился!')
            JOINT = True
            testInputData[i]['time'] = datetime.strptime(
                testInputData[i]['time'], "%Y-%m-%d %H:%M:%S.%f")
            dictSegment[currentSegment].append(testInputData[i])
        else:
            print('Построение отрезка!')
            JOINT = False
            testInputData[i]['time'] = datetime.strptime(
                testInputData[i]['time'], "%Y-%m-%d %H:%M:%S.%f")
            dictSegment[currentSegment].append(testInputData[i])

    # Расчет растояния
    distance = 0
    for segment in dictSegment:
        if len(dictSegment[segment]) > 1:
            dTime = (dictSegment[segment][1]['time'] -
                     dictSegment[segment][0]['time']).total_seconds()
            dictSegment[segment][0]['distance'] = distance + \
                dictSegment[segment][0]['speed'] * dTime
            distance += dictSegment[segment][0]['speed'] * dTime
        else:
            print('Сегмент состоит из одного кадра!')
        for i in range(1, len(dictSegment[segment])):
            dTime = (dictSegment[segment][i]['time'] -
                     dictSegment[segment][i-1]['time']).total_seconds()
            dictSegment[segment][i]['distance'] = distance + \
                dictSegment[segment][i]['speed'] * dTime
            distance += dictSegment[segment][i]['speed'] * dTime
    dictSegment[len(dictSegment)][-1]['distance'] = distance

    return dictSegment


def sow_conv(dictSegment: dict) -> None:
    listX = []
    for segment in dictSegment.values():
        tempList = []
        for cadr in segment:
            tempList.append(cadr['distance'])
        listX.append(tempList)

    listLeftY = []
    for segment in dictSegment.values():
        tempList = []
        for cadr in segment:
            tempList.append(cadr['lr'][1])
        listLeftY.append(tempList)

    listRightY = []
    for segment in dictSegment.values():
        tempList = []
        for cadr in segment:
            tempList.append(cadr['lr'][1] + cadr['wc'][1])
        listRightY.append(tempList)

    for i in range(len(listLeftY)):
        plt.plot(listLeftY[i], listX[i], listRightY[i], listX[i])
    plt.title("Сравнение")  # заголовок
    plt.ylabel("Синие точки", fontsize=14)  # ось ординат
    plt.grid(True)  # включение отображение сетки
    plt.show()

ауауа
пукпк
with open("data.json", "r") as read_file:
    a = callback(read_file.read())
    searh_point(a, 5)
