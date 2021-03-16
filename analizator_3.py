import matplotlib.pyplot as plt
from DBcm import UseDatabase, ConnectError, CredentialsError, SQLError


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
        print('Деление на блоки')
        tempList = list()
        self.lenghtBlock = self.lenghtLenta / self.countBlock
        iBlock = 1
        for cadr in self.listCadr:
            if cadr['distance'] < self.lenghtBlock * iBlock:
                tempList.append(cadr)

            elif cadr['distance'] == self.lenghtBlock * iBlock:
                tempList.append(cadr)
                joint = tempList[-1]
                self.listBlocks.append(tempList.copy())
                tempList.clear()
                tempList.append(joint)
                iBlock += 1

            else:
                joint = tempList[-1]
                joint['distance'] = iBlock * self.lenghtBlock
                self.listBlocks.append(tempList.copy())
                tempList.clear()
                tempList.append(joint)
                tempList.append(cadr)
                iBlock += 1

        print(tempList)

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
        print('Деление на блоки завершено')

    def callback(self, body) -> None:
        """Метод сбора данных из пакета пришедшего с RabbitMQ.
           Данные должны приходить в формате JSON.
        """
        inputData = eval(body)
        self.listAllCadr.append(inputData)
        if self.findLoop:
            print('*')
            # distance = self.listNewCadr[-1]['distance']
            # iBlock = 1
            # for iCadr in range(len(self.listNewCadr)):
            #     if self.listNewCadr[iCadr]['distance'] >= self.lenghtBlock * iBlock:
            #         print('Новый блок!')
            #         self.listNewBlocks.append(self.listNewCadr[:iCadr])
            #         iBlock += 1
            #         break
            # print(self.listNewBlocks)
            # for iCadr in inputData:
            #     print(inputData[iCadr])
            #     self.listNewCadr.append(inputData[iCadr])
            #     self.listNewCadr[-1]['distance'] = distance + inputData[iCadr]['speed'] * self.FPS
            #     distance += inputData[iCadr]['speed'] * self.FPS

            #     tempList = list()
            #     iBlock = 1
            #     for cadr in self.listNewCadr:
            #         if cadr['distance'] < self.lenghtBlock * iBlock:
            #             tempList.append(cadr)

            #         elif cadr['distance'] == self.lenghtBlock * iBlock:
            #             tempList.append(cadr)
            #             joint = tempList[-1]
            #             self.listNewBlocks.append(tempList.copy())
            #             tempList.clear()
            #             tempList.append(joint)
            #             iBlock += 1

            #         else:
            #             joint = tempList[-1]
            #             joint['distance'] = iBlock * self.lenghtBlock
            #             self.listNewBlocks.append(tempList.copy())
            #             tempList.clear()
            #             tempList.append(joint)
            #             tempList.append(cadr)
            #             iBlock += 1
            #     self.listNewCadr.clear()

            
                # if self.listNewCadr[-1]['distance'] >= self.lenghtBlock:
                #     print('Создан новый блок', self.listNewCadr)
                #     self.listNewBlocks.append(self.listNewCadr.copy())

                # if inputData[iCadr]['marker']:
                #     print('Повторение круга')
                #     self.iEnd = iCadr
                #     self.iEndSet = len(self.listAllCadr)-1
                #     break

                #     for iSet in range(self.iEndSet+1):
                #         for iCadr in self.listAllCadr[iSet]:
                #             self.listNewCadr.append(self.listAllCadr[iSet][iCadr])
                #             self.listNewCadr[-1]['distance'] = distance + \
                #                 self.listAllCadr[iSet][iCadr]['speed'] * self.FPS
                #             distance += self.listAllCadr[iSet][iCadr]['speed'] * self.FPS

                #             if self.listNewCadr[-1]['marker']:
                #                 self.lenghtLenta = self.listNewCadr[-1]['distance']
                #                 print('Круг записан')
                #                 break

        else:
            distance = 0
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
                        print('Круг построен')
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
                                        print('Круг записан')
                                        self.division_blocks()

                                        distance = 0
                                        self.listNewCadr.append(self.listAllCadr[iSet][iCadr].copy())
                                        self.listNewCadr[-1]['distance'] = distance

                                        iBlock = 1
                                        iStarBlock = 0
                                        for iCadrLeft in list(self.listAllCadr[iSet].keys())[iCadr+1:]:
                                            self.listNewCadr.append(self.listAllCadr[iSet][iCadrLeft])
                                            self.listNewCadr[-1]['distance'] = distance + self.listAllCadr[iSet][iCadrLeft]['speed'] * self.FPS
                                            distance += self.listAllCadr[iSet][iCadrLeft]['speed'] * self.FPS
                                            if distance >= self.lenghtBlock * iBlock:
                                                print('Новый блок!')
                                                self.listNewBlocks.append(self.listNewCadr[iStarBlock:iCadrLeft])
                                                iStarBlock = iCadrLeft
                                                iBlock += 1
                                        print('Остальные кадры записаны в listNewCadr')
                                        self.listAllCadr.clear()
                                        break
                        break
                # if self.findLoop:
                #     self.division_blocks()

    # def create_block(self, cadr):
    #     print(cadr)



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

    print('длина ленты', lenta.lenghtLenta)
    print('длина блока', lenta.lenghtBlock)
    # print(len(lenta.listCadr))
    # for i in lenta.listNewCadr:
    #     print(i)
    print(len(lenta.listBlocks))
    for i in lenta.listBlocks:
        print(i)
    # lenta.division_blocks()
    # lenta.find_loop(listSegments, 170, 190)
    # lenta.sow_conv()
