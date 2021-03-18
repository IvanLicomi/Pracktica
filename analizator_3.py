import matplotlib.pyplot as plt
import pika
from DBcm import UseDatabase, ConnectError, CredentialsError, SQLError


class Block:
    """Класс для хранения информации о блоке летны. Состоит из следующих параметров:
       index - позиция блока на ленте
       lmax, lmin, rmax, rmin - параметры блока
       start - координата начала блока
       end - координата конца блока
       cadrs - словарь кадров из которых состоит блок
       wracks - словарь повреждений блока
    """
    def __init__(self, index: int, start: int, end: int, cadrs: dict):
        self.index = index
        self.start = start
        self.end = end
        self.cadrs = cadrs
        # self.wracks = wracks

        self.lmax = self.cadrs[0]['lmax']
        self.lmin = self.cadrs[0]['lmin']
        self.rmax = self.cadrs[0]['rmax']
        self.rmin = self.cadrs[0]['rmin']

        for i in self.cadrs[1:]:
            if i['lmax'] > self.lmax:
                self.lmax = i['lmax']
            if i['lmin'] < self.lmin:
                self.lmin = i['lmin']
            if i['rmax'] > self.rmax:
                self.rmax = i['rmax']
            if i['rmin'] < self.rmin:
                self.rmin = i['rmin']

    def __str__(self):
        return str(self.index) + ' блок'
                

class Lenta:
    """"""
    def __init__(self, DBCONFIG: dict, FPS: int, countBlock: int, dMin: int):
        self.DBCONFIG = DBCONFIG # Параметры подключения к БД
        self.FPS = 1/FPS # Количество кадров в секунду камеры
        self.countBlock = countBlock # Количество болоков на которое будет разделена лента
        self.dMin = dMin

        self.listAllCadr = list() # Список кадров для создания первого оборота 
        self.listCadr = list() # Кадры текущего оборота
        self.listNewCadr = list() # Кадры нового оборота
        self.listBlocks = list() # Список блоков текущего оборотов
        self.listNewBlocks = list() # Список блоков нового оборота
        self.listWract = list() # Хз

        self.lenghtBlock = 0 # Длина одного блока. Вычисляется после построения полного оборота.
        self.lenghtLenta = 0 # Длина одного оборота ленты. Вычисляется после построения полного оборота.

        self.findStartLoop = False
        self.findLoop = False
        self.checkNewCadr = False

        self.iCurrentBlock = 0
        self.iStart = 0
        self.iStartSet = 0
        self.iEnd = 0
        self.iEndSet = 0

    def loadDataBase(self, inputData: list, CurrentData: list) -> list:
        """Отправляет данные в БД, если есть отличия."""
        if inputData != CurrentData:
            try:
                with UseDatabase(DBCONFIG) as cursor:
                    _SQl = """INSERT INTO lenta_conv(comment)
                            VALUES ('Обнаружены изенения')"""
                    cursor.execute(
                        _SQl)  # 'Обнаружены изенения в {0} сегменте'.format(segmentCurrent))

                return inputData

            except ConnectError as err:
                print('Is your database switched on? Error: ', str(err))
            except CredentialsError as err:
                print('User-id/Password issues. Error: ', str(err))
            except SQLError as err:
                print('Is your query correct? Error: ', str(err))
            return 'Error'
        else:
            return CurrentData

    def division_blocks(self):
        """Метод делит ленту на блоки равного размера."""
        print('[*] - деление на блоки')
        tempList = list()
        self.lenghtBlock = self.lenghtLenta / self.countBlock
        iBlock = 1
        for cadr in self.listCadr:
            if cadr['distance'] < self.lenghtBlock * iBlock:
                tempList.append(cadr)

            elif cadr['distance'] == self.lenghtBlock * iBlock:
                tempList.append(cadr)
                joint = tempList[-1]
                self.listBlocks.append(Block(self.iCurrentBlock, tempList[0]['distance'], self.lenghtBlock * iBlock, tempList))
                self.iCurrentBlock += 1
                tempList.clear()
                tempList.append(joint)
                iBlock += 1

            else:
                joint = tempList[-1]
                joint['distance'] = iBlock * self.lenghtBlock
                self.listBlocks.append(Block(self.iCurrentBlock, tempList[0]['distance'], self.lenghtBlock * iBlock, tempList))
                self.iCurrentBlock += 1
                tempList.clear()
                tempList.append(joint)
                tempList.append(cadr)
                iBlock += 1
        self.iCurrentBlock = 0       
        # for iBlock in range(len(self.listBlocks)):
        #     tempDict = dict()
        #     lmaxWrack = 0
        #     rmaxWrack = 0

        #     for cadr in self.listBlocks[iBlock]:
        #         if cadr['lmax'] - cadr['lmin'] >= lmaxWrack:
        #             lmaxWrack = cadr['lmax'] - cadr['lmin']
        #             tempDict['wrack'] = lmaxWrack
        #             tempDict['distance'] = cadr['distance']
        #             tempDict['side'] = 'left'
        #             tempDict['index'] = iBlock

        #         if cadr['rmax'] - cadr['rmin'] >= rmaxWrack:
        #             rmaxWrack = cadr['rmax'] - cadr['rmin']
        #             tempDict['wrack'] = rmaxWrack
        #             tempDict['distance'] = cadr['distance']
        #             tempDict['side'] = 'right'
        #             tempDict['index'] = iBlock

        #     if lmaxWrack >= self.dMin or rmaxWrack >= self.dMin:
        #         self.listWract.append(tempDict)
        print('[*] - деление на блоки завершено')
    
    def find_loop(self, inputData):
        distance = 0
        print('[*] - построение круга')
        if self.findStartLoop == False:
            for i in inputData:
                if inputData[i]['marker']:
                    self.findStartLoop = True
                    self.iStart = i
                    self.iStartSet = len(self.listAllCadr)-1
                    break
        else:
            for i in inputData:
                if inputData[i]['marker'] and self.findLoop == False:
                    print('[*] - круг построен')
                    self.iEnd = i
                    self.iEndSet = len(self.listAllCadr)-1
                    self.findLoop = True
                    self.listCadr.append(self.listAllCadr[self.iStartSet][self.iStart])
                    self.listCadr[0]['distance'] = distance

                    for iSet in range(self.iStartSet, self.iEndSet+1):
                        if iSet == self.iStartSet:
                            for iCadr in list(self.listAllCadr[iSet].keys())[self.iStart+1:]:
                                self.listCadr.append(self.listAllCadr[iSet][iCadr])
                                self.listCadr[-1]['distance'] = distance + self.listAllCadr[iSet][iCadr]['speed'] * self.FPS
                                distance += self.listAllCadr[iSet][iCadr]['speed'] * self.FPS
                        else:
                            for iCadr in self.listAllCadr[iSet]:
                                self.listCadr.append(self.listAllCadr[iSet][iCadr])
                                self.listCadr[-1]['distance'] = distance + self.listAllCadr[iSet][iCadr]['speed'] * self.FPS
                                distance += self.listAllCadr[iSet][iCadr]['speed'] * self.FPS

                                if self.listCadr[-1]['marker']:
                                    self.lenghtLenta = self.listCadr[-1]['distance']
                                    self.division_blocks()

                                    distance = 0
                                    self.listNewCadr.append(self.listAllCadr[iSet][iCadr].copy())
                                    self.listNewCadr[-1]['distance'] = distance

                                    for iCadrLeft in list(self.listAllCadr[iSet].keys())[iCadr+1:]:
                                        self.listNewCadr.append(self.listAllCadr[iSet][iCadrLeft])
                                        self.listNewCadr[-1]['distance'] = distance + self.listAllCadr[iSet][iCadrLeft]['speed'] * self.FPS
                                        distance += self.listAllCadr[iSet][iCadrLeft]['speed'] * self.FPS
                                    print('[*] - Остальные кадры записаны в listNewCadr')
                                    self.checkNewCadr = False
                                    self.listAllCadr.clear()
                                    break
                    break

    def callback(self, body) -> None:
        """Метод сбора данных из пакета пришедшего с RabbitMQ.
           Данные должны приходить в формате JSON.
        """
        if self.findLoop:
            print('[*] - запуск главного процесса')
            if self.listNewCadr and not self.checkNewCadr: # Обработка оставшихся кадров в наборе (создание или наполнение блока), если они есть и не было обработки.
                print('[*] - обработка оставшихся кадров')
                iBlock = 1
                tempList = list()
                for iCadr in range(len(self.listNewCadr)):
                    if self.listNewCadr[iCadr]['distance'] < self.lenghtBlock * iBlock:
                        tempList.append(self.listNewCadr[iCadr])

                    elif self.listNewCadr[iCadr]['distance'] == self.lenghtBlock * iBlock:
                        tempList.append(self.listNewCadr[iCadr])
                        joint = tempList[-1]
                        self.listNewBlocks.append(Block(self.iCurrentBlock, tempList[0]['distance'], self.lenghtBlock * iBlock, tempList))
                        tempList.clear()
                        tempList.append(joint)
                        iBlock += 1

                    else:
                        joint = tempList[-1]
                        joint['distance'] = iBlock * self.lenghtBlock
                        self.listNewBlocks.append(Block(self.iCurrentBlock, tempList[0]['distance'], self.lenghtBlock * iBlock, tempList))
                        self.iCurrentBlock += 1
                        tempList.clear()
                        tempList.append(joint)
                        tempList.append(self.listNewCadr[iCadr])
                        iBlock += 1

                self.listNewCadr = tempList.copy()
                self.checkNewCadr = True

                if self.listNewBlocks:
                    self.comparison_bloks()
                else:
                    self.callback(body)
            else:
                print('[*] - a')
                inputData = eval(body)
                for i in inputData:
                    print(inputData[i])
                print('*'*100)

        else:
            inputData = eval(body)
            self.listAllCadr.append(inputData)
            self.find_loop(inputData)
            
    def comparison_bloks(self):
        print('[*] - сравнение блоков')
        
        for i in range(len(self.listNewBlocks)):
            differences = False
            # for k, j in self.listNewBlocks[i].__dict__.values():
            #     if 
            if self.listNewBlocks[i].lmax != self.listBlocks[i].lmax:
                differences = True
            if self.listNewBlocks[i].lmin != self.listBlocks[i].lmin:
                differences = True
            if self.listNewBlocks[i].rmax != self.listBlocks[i].rmax:
                differences = True
            if self.listNewBlocks[i].rmin != self.listBlocks[i].rmin:
                differences = True
            if differences:
                print('Обнаружены изменения')
            else:
                print('Изменения не обнаружены')


DBCONFIG = {'host': '192.168.1.254',
            'user': 'user2',
            'password': '0011',
            'database': 'videoai', }

cs = int(input("Количество блоков: "))
lenta = Lenta(DBCONFIG, 15, cs, 7)

# with open("data_copy.json", "r") as read_file:
#     lenta.callback(read_file.read())
with open("data.json", "r") as read_file:
    lenta.callback(read_file.read())
with open("data_copy_2.json", "r") as read_file:
    lenta.callback(read_file.read())
with open("data.json", "r") as read_file:
    lenta.callback(read_file.read())

# with open("data_copy_2.json", "r") as read_file:
#     lenta.callback(read_file.read())

with open("data.json", "r") as read_file:
    lenta.callback(read_file.read())
with open("data_copy_2.json", "r") as read_file:
    lenta.callback(read_file.read())

print('длина ленты', lenta.lenghtLenta)
print('длина блока', lenta.lenghtBlock)
