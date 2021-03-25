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
        self.DBCONFIG = DBCONFIG  # Параметры подключения к БД
        self.FPS = 1/FPS  # Количество кадров в секунду камеры
        self.countBlock = countBlock  # Количество болоков на которое будет разделена лента
        self.dMin = dMin

        self.listCadr = list()  # Кадры текущего оборота
        self.listNewCadr = list()  # Кадры нового оборота
        self.listBlocks = list()  # Список блоков текущего оборотов
        self.listNewBlocks = list()  # Список блоков нового оборота
        self.listWract = list()  # Хз

        # Длина одного блока. Вычисляется после построения полного оборота.
        self.lenghtBlock = 0
        # Длина одного оборота ленты. Вычисляется после построения полного оборота.
        self.lenghtLenta = 0

        self.findStartLoop = False
        self.findLoop = False
        self.checkNewCadr = False

        self.iCurrentBlock = 0
        self.iStart = 0
        self.iStartSet = 0
        self.iEnd = 0
        self.iEndSet = 0

    # Доделать!
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
    # Сделано

    def division_blocks(self, listCadr, listBlocks):
        """Метод делит ленту на блоки равного размера."""
        tempList = list()
        for cadr in listCadr:
            iBlock = self.iCurrentBlock + 1
            if cadr['distance'] < self.lenghtBlock * iBlock:
                tempList.append(cadr)

            elif cadr['distance'] == self.lenghtBlock * iBlock:
                tempList.append(cadr)
                listBlocks.append(Block(
                    self.iCurrentBlock, self.lenghtBlock * (iBlock-1), self.lenghtBlock * iBlock, tempList.copy()))
                self.iCurrentBlock += 1
                tempList.clear()

            else:
                listBlocks.append(Block(
                    self.iCurrentBlock, self.lenghtBlock * (iBlock-1), self.lenghtBlock * iBlock, tempList.copy()))
                self.iCurrentBlock += 1
                tempList.clear()
                tempList.append(cadr)
        return tempList.copy()
    # Сделано
    def find_loop(self, inputData):
        distance = 0
        print('[*] - построение круга')
        if self.findStartLoop == False:
            for i in inputData:
                if inputData[i]['marker']:
                    self.findStartLoop = True
                    self.iStart = i
                    self.iStartSet = len(self.listNewCadr)-1
                    break
        else:
            for i in inputData:
                if inputData[i]['marker'] and self.findLoop == False:
                    print('[*] - круг построен')
                    self.iEnd = i
                    self.iEndSet = len(self.listNewCadr)-1
                    self.findLoop = True
                    self.listCadr.append(
                        self.listNewCadr[self.iStartSet][self.iStart])
                    self.listCadr[0]['distance'] = distance

                    for iSet in range(self.iStartSet, self.iEndSet+1):
                        if iSet == self.iStartSet:
                            for iCadr in list(self.listNewCadr[iSet].keys())[self.iStart+1:]:
                                self.listCadr.append(
                                    self.listNewCadr[iSet][iCadr])
                                self.listCadr[-1]['distance'] = distance + \
                                    self.listNewCadr[iSet][iCadr]['speed'] * self.FPS
                                distance += self.listNewCadr[iSet][iCadr]['speed'] * self.FPS
                        else:
                            for iCadr in self.listNewCadr[iSet]:
                                self.listCadr.append(
                                    self.listNewCadr[iSet][iCadr])
                                self.listCadr[-1]['distance'] = distance + \
                                    self.listNewCadr[iSet][iCadr]['speed'] * self.FPS
                                distance += self.listNewCadr[iSet][iCadr]['speed'] * self.FPS

                                if self.listCadr[-1]['marker']:
                                    # Деление нового оброта на блоки
                                    self.lenghtLenta = self.listCadr[-1]['distance']
                                    self.lenghtBlock = self.lenghtLenta / self.countBlock
                                    self.division_blocks(
                                        self.listCadr, self.listBlocks)
                                    self.iCurrentBlock = 0
                                    # Обработка оставшихся кадров в наборе
                                    distance = 0
                                    tempListCadr = list()
                                    tempListCadr.append(
                                        self.listNewCadr[iSet][iCadr].copy())
                                    tempListCadr[-1]['distance'] = distance

                                    for iCadrLeft in list(self.listNewCadr[iSet].keys())[iCadr+1:]:
                                        tempListCadr.append(
                                            self.listNewCadr[iSet][iCadrLeft])
                                        tempListCadr[-1]['distance'] = distance + \
                                            self.listNewCadr[iSet][iCadrLeft]['speed'] * self.FPS
                                        distance += self.listNewCadr[iSet][iCadrLeft]['speed'] * self.FPS
                                    print(
                                        '[*] - Остальные кадры записаны в listNewCadr')
                                    self.checkNewCadr = False
                                    self.listNewCadr.clear()
                                    self.listNewCadr = tempListCadr.copy()
                                    tempListCadr.clear()
                                    break
                    break
    # Доделать!

    def callback(self, body) -> None:
        """Метод сбора данных из пакета пришедшего с RabbitMQ.
           Данные должны приходить в формате JSON.
        """
        if self.findLoop:  # Если полный оборот построен, то обрабатываем данные для последующего сравнения
            print('[*] - запуск главного процесса')
            # Обработка оставшихся кадров после постоения оборота, если они есть и не было обработки.
            if self.listNewCadr and not self.checkNewCadr:
                print('[*] - обработка оставшихся кадров')
                self.listNewCadr = self.division_blocks(
                    self.listNewCadr, self.listNewBlocks)
                self.checkNewCadr = True
                if self.listNewBlocks:
                    self.comparison_bloks()
            else:
                print('[*] - сбор данных')
                inputData = eval(body)

                if self.listNewCadr:
                    distance = self.listNewCadr[-1]['distance']
                else:
                    distance = 0

                for iCadr in inputData:
                    self.listNewCadr.append(inputData[iCadr])
                    self.listNewCadr[-1]['distance'] = distance + \
                        inputData[iCadr]['speed'] * self.FPS
                    distance += inputData[iCadr]['speed'] * self.FPS

                    if self.listNewCadr[-1]['marker']:
                        print('Полный оборот')
                        if self.listNewCadr[-1]['distance'] != self.lenghtLenta:
                            print('Обнаружено несоотвествие длины ленты. Размер несотвествия:  ', abs(
                                self.lenghtLenta - self.listNewCadr[-1]['distance']))
                            # Растягивание или сжатие блоков
                            if abs(self.lenghtLenta - self.listNewCadr[-1]['distance']) < self.lenghtLenta * 0.05:
                                change = (self.listNewCadr[-1]['distance'] - self.lenghtLenta) / 2 / len(self.listCadr)
                                print('Погрешность меньше 5%')

                                for i in range(1, len(self.listCadr[1:])+1):
                                    x = change * i + change
                                    self.listCadr[i]['distance'] += x

                                self.listBlocks.clear()
                                self.lenghtBlock += (self.listNewCadr[-1]['distance'] - self.lenghtLenta) / 2 / self.countBlock
                                self.lenghtLenta += (self.listNewCadr[-1]['distance'] - self.lenghtLenta) / 2
                                
                                self.iCurrentBlock = 0
                                self.division_blocks(self.listCadr, self.listBlocks)
                                self.iCurrentBlock = 0
                            else:
                                print('Погрешность больше 5%')
                        else:
                            print('Несоотвествие длины не обнаружено')
                            self.listNewCadr = self.division_blocks(self.listNewCadr, self.listNewBlocks)
                            self.comparison_bloks()
                            tempListCadr = list()
                            tempListCadr.append(inputData[iCadr])
                            tempListCadr[-1]['distance'] = distance

                            for i in list(inputData)[iCadr+1:]:
                                tempListCadr.append(inputData[i])
                                tempListCadr[-1]['distance'] = distance + \
                                    inputData[i]['speed'] * self.FPS
                                distance += inputData[i]['speed'] * self.FPS

                            self.listNewCadr.clear()
                            self.listNewCadr = tempListCadr.copy()
                            tempListCadr.clear()
                        break

                    if self.listNewCadr[-1]['distance'] >= self.lenghtBlock * len(self.listNewBlocks):
                        self.listNewCadr = self.division_blocks(
                            self.listNewCadr, self.listNewBlocks)
                        if len(self.listNewBlocks) > len(self.listBlocks):
                            print('Что-то нето. Новых блоков больше, чем старых')
                        else:
                            self.comparison_bloks()

        else:  # Если полный оборот не построен, то передаем данные для построения оборота
            inputData = eval(body)
            self.listNewCadr.append(inputData)
            self.find_loop(inputData)
    # Доделать! Запись в БД.
    #

    def comparison_bloks(self):
        print('[*] - сравнение блоков')
        for i in range(len(self.listNewBlocks)):
            differences = False
            if self.listNewBlocks[i].lmax != self.listBlocks[i].lmax:
                differences = True
            if self.listNewBlocks[i].lmin != self.listBlocks[i].lmin:
                differences = True
            if self.listNewBlocks[i].rmax != self.listBlocks[i].rmax:
                differences = True
            if self.listNewBlocks[i].rmin != self.listBlocks[i].rmin:
                differences = True
            if differences:
                print('Обнаружены изменения в ', self.listNewBlocks[i])
                # Запись в БД новой конфигурации
            # else:
            #     print('Изменения не обнаружены')


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
with open("data_2.json", "r") as read_file:
    lenta.callback(read_file.read())
with open("data1.json", "r") as read_file:
    lenta.callback(read_file.read())
with open("data_2.json", "r") as read_file:
    lenta.callback(read_file.read())

print('длина ленты', lenta.lenghtLenta)
print('длина блока', lenta.lenghtBlock)
