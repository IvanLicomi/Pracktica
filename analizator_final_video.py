import matplotlib.pyplot as plt
from mq import mq
from DBcm import UseDatabase, ConnectError, CredentialsError, SQLError


class Block:
    """Класс для хранения информации о блоке летны. Состоит из следующих параметров:
       index - позиция блока на ленте
       maxLeft, minLeft, maxRight, minRight - параметры блока
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
        self.maxLeft = self.cadrs[0]['maxLeft']
        self.minLeft = self.cadrs[0]['minLeft']
        self.maxRight = self.cadrs[0]['maxRight']
        self.minRight = self.cadrs[0]['minRight']
        self.width = self.cadrs[0]['dCenter'] # хз

        for i in self.cadrs[1:]:
            if i['maxLeft'] > self.maxLeft:
                self.maxLeft = i['maxLeft']
            if i['minLeft'] < self.minLeft:
                self.minLeft = i['minLeft']
            if i['maxRight'] > self.maxRight:
                self.maxRight = i['maxRight']
            if i['minRight'] < self.minRight:
                self.minRight = i['minRight']

        self.maxWidth = self.maxLeft - self.maxRight
        self.minWidth = self.minLeft - self.minRight

        self.dRight = self.maxLeft - self.minLeft
        self.dLeft = self.maxRight - self.minRight

    def __str__(self):
        return str(self.index) + ' блок'


class Lenta:
    """"""

    def __init__(self, DBCONFIG: dict, FPS: int, countBlock: int, approximateLenght: int):
        self.DBCONFIG = DBCONFIG  # Параметры подключения к БД
        self.FPS = 1/FPS  # Количество кадров в секунду камеры
        self.countBlock = countBlock  # Количество болоков на которое будет разделена лента
        # self.dMin = dMin
        self.minLentaLenght = approximateLenght - approximateLenght * 0.05
        self.maxLentaLenght = approximateLenght + approximateLenght * 0.05

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
        self.findMin = False
        self.findMax = False

        self.distance = 0
        self.iCurrentBlock = 0
        self.iStartSet = 0
        self.iEndSet = 0
        self.last_id_conv = 0

        


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
    
    def division_blocks(self, listCadr, listBlocks):
        """Метод делит ленту на блоки равного размера."""
        tempList = list()
        for cadr in listCadr:
            # print(cadr)
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

    def find_loop(self, inputData):
        for i in inputData: i['speed'] = 1
        if self.findStartLoop == False:
            if self.distance == 0:
                self.listNewCadr.append(inputData[0].copy())
                self.listNewCadr[0]['distance'] = 0

            if len(self.listNewCadr) == 1:
                for cadr in inputData[1:]:
                    self.listNewCadr.append(cadr.copy())
                    self.listNewCadr[-1]['distance'] = self.distance + self.listNewCadr[-1]['speed'] * self.FPS
                    self.distance += self.listNewCadr[-1]['speed'] * self.FPS
            else:
                tempListCadr = list()
                for i, cadr in enumerate(inputData):
                    self.listNewCadr.append(cadr.copy())
                    self.listNewCadr[-1]['distance'] = self.distance + self.listNewCadr[-1]['speed'] * self.FPS
                    self.distance += self.listNewCadr[-1]['speed'] * self.FPS
                    if self.listNewCadr[-1]['distance'] >= self.minLentaLenght and self.findMin == False:
                        self.iStartSet = len(self.listNewCadr)-1
                        self.findMin = True
                    if self.listNewCadr[-1]['distance'] >= self.maxLentaLenght and self.findMax == False:
                        self.iEndSet = len(self.listNewCadr)-1
                        self.findMax = True
                        tempListCadr = inputData[i:]
                        break
            print(self.listNewCadr[-1]['distance'])
            n = 0
            start = 0
            if self.findMax:
                self.findMin = False
                self.findMax = False
                for i, cadr in enumerate(self.listNewCadr[self.iStartSet:self.iEndSet]):
                    if (cadr['wc'][1] == self.listNewCadr[n]['wc'][1] and cadr['lr'][1] == self.listNewCadr[n]['lr'][1] and 
                        cadr['rr'][1] == self.listNewCadr[n]['rr'][1]):
                        if n == 0: start = i
                        n += 1
                        print('+', n, '/', len(self.listNewCadr[self.iStartSet:self.iEndSet]) // 3)
                        if len(self.listNewCadr[self.iStartSet:self.iEndSet]) // 3 <= n:
                            self.lenghtLenta = self.listNewCadr[start+self.iStartSet]['distance']
                            self.lenghtBlock = self.lenghtLenta / self.countBlock
                            self.listCadr = self.listNewCadr[:start+self.iStartSet+1]
                            self.division_blocks(self.listCadr, self.listBlocks)
                            self.listNewCadr = self.listNewCadr[start+self.iStartSet:start+self.iEndSet] + tempListCadr.copy()
                            for n in self.listNewCadr: n.pop('distance', None)
                            self.iCurrentBlock = 0
                            self.findLoop = True
                            print('Круг построен')
                            print('длина ленты', self.lenghtLenta)
                            print('длина блока', self.lenghtBlock)
                            with UseDatabase(self.DBCONFIG) as cursor:
                                _SQl = """INSERT INTO lenta_conv(block_length, lenta_length) VALUES (%s, %s)"""
                                cursor.execute(_SQl, (self.lenghtBlock, self.lenghtLenta))
                            with UseDatabase(self.DBCONFIG) as cursor:
                                _SQl = """SELECT MAX(`id`) FROM `lenta_conv`"""
                                self.last_id_conv = cursor.execute(_SQl) 
                                if self.last_id_conv == None:
                                    self.last_id_conv == 0
                                else:
                                    self.last_id_conv += 1
                                
                                for block in self.listBlocks:
                                    with UseDatabase(self.DBCONFIG) as cursor:
                                        _SQl = """INSERT INTO lenta_blocks(id_conv, dLeft, dRight, minWidth, maxWidth)
                                                VALUES (%s, %s, %s, %s, %s)"""
                                        cursor.execute(_SQl, (self.last_id_conv, block.dLeft, block.dRight, block.minWidth, block.maxWidth))  
                            break

                if len(self.listBlocks) != 0 and len(self.listNewCadr) != 0:
                        self.distance = 0
                        self.listNewCadr[0]['distance'] = 0
                        for i in self.listNewCadr[1:]:
                            i['distance'] = self.distance + i['speed'] * self.FPS
                            self.distance += i['speed'] * self.FPS
                        self.listNewCadr = self.division_blocks(self.listNewCadr, self.listNewBlocks)
                        if self.listNewBlocks:
                            self.comparison_bloks()
                else:
                    print('Круг не найден')
                    self.maxLentaLenght += self.maxLentaLenght - self.minLentaLenght
    # Доделать!                    
    def callback(self, routing_key, body) -> None:
        """Метод сбора данных из пакета пришедшего с RabbitMQ.
           Данные должны приходить в формате JSON.
        """
        if self.findLoop:  # Если полный оборот построен, то обрабатываем данные для последующего сравнения
            print('[*] - сбор данных')
            tempData = eval(body)
            inputData = [{**tempData['points'][i], **tempData['cords'][i]} for i in tempData['points']]
            for i in inputData: i['speed'] = 1

            if self.listNewCadr:
                self.distance = self.listNewCadr[-1]['distance']
            else:
                self.distance = 0

            tempListCadr = list()
            for i, cadr in enumerate(inputData):
                self.listNewCadr.append(cadr.copy())
                self.listNewCadr[-1]['distance'] = self.distance + self.listNewCadr[-1]['speed'] * self.FPS
                self.distance += self.listNewCadr[-1]['speed'] * self.FPS
                

                # Создание нового болка
                if self.listNewCadr[-1]['distance'] >= self.lenghtBlock * self.iCurrentBlock:
                    self.listNewCadr = self.division_blocks(self.listNewCadr, self.listNewBlocks)
                    # Отпраление индекса текщего блока

                # Поиск повторения круга
                if len(self.listNewBlocks) == self.countBlock:
                    if self.listNewBlocks[-1].cadrs[-1]['distance'] >= self.minLentaLenght and self.findMin == False:
                        self.findMin = True
                    elif self.listNewBlocks[-1].cadrs[-1]['distance'] >= self.maxLentaLenght and self.findMax == False:
                        self.findMax = True
                        tempListCadr = inputData[i:]
                        print('Найден верхний предел. 0')
                        break

                if len(self.listNewCadr) != 0:
                    if self.listNewCadr[-1]['distance'] >= self.minLentaLenght and self.findMin == False:
                        self.findMin = True
                    elif self.listNewCadr[-1]['distance'] >= self.maxLentaLenght and self.findMax == False:
                        self.findMax = True
                        tempListCadr = inputData[i:]
                        print('Найден верхний предел. 1')
                        break
                else:
                    if self.listNewBlocks[-1].cadrs[-1]['distance'] >= self.minLentaLenght and self.findMin == False:
                        self.findMin = True
                    elif self.listNewBlocks[-1].cadrs[-1]['distance'] >= self.maxLentaLenght and self.findMax == False:
                        self.findMax = True
                        tempListCadr = inputData[i:]
                        print('Найден верхний предел. 2')
                        break

            if self.findMax:
                
                n = 0
                coincidence = 0
                loop = False
                print('Повторение круга')
                self.findMin = False
                self.findMax = False
                tempList = self.listNewBlocks[-1].cadrs + self.listNewCadr
                marker = 0

                while loop == False and n < len(self.listCadr)*0.2:
                    for i, cadr in enumerate(tempList[n]):
                        if (cadr['maxLeft'] == self.listCadr[n]['maxLeft'] and cadr['minLeft'] == self.listCadr[n]['minLeft'] and 
                            cadr['maxRight'] == self.listCadr[n]['maxRight'] and cadr['minRight'] == self.listCadr[n]['minRight']):
                            if coincidence == 0: start = i
                            print('+', coincidence, '/', len(tempList) // 2.2)
                            coincidence += 1
                            if len(tempList) // 2.2 <= coincidence:
                                for block in self.listNewBlocks:
                                    for _ in block.cadrs:
                                        marker += 1
                                marker += start
                                loop = True
                                break
                    n += 1
                if loop:
                    p = []
                    for i in self.listNewBlocks[:-1]:
                        p += i.cadrs
                    p += tempList
                    print('Несоотвествие длины не обнаружено', p[marker-2])
                    print(marker, len(p))
                    self.listCadr = p[:marker]
                    self.comparison_bloks()
                    self.listNewBlocks.clear()
                    self.listNewCadr = tempListCadr.copy()
                    if len(self.listNewCadr) >= 1:
                        for n in self.listNewCadr: n.pop('distance', None)
                        self.distance = 0
                        self.listNewCadr[0]['distance'] = self.distance
                        for j in self.listNewCadr[1:]:
                            j['distance'] = self.distance + j['speed'] * self.FPS
                            self.distance += j['speed'] * self.FPS
                        self.listNewCadr = self.division_blocks(self.listNewCadr, self.listNewBlocks)
                        print(self.listNewBlocks)
                        print('fef')
                    self.iCurrentBlock = 0
        else:  # Если полный оборот не построен, то передаем данные для построения оборота
            tempData = eval(body)
            inputData = [{**tempData['points'][i], **tempData['cords'][i]} for i in tempData['points']]
            self.find_loop(inputData)
    # Доделать! Запись в БД.
    def comparison_bloks(self):
        print('[*] - Сравнение')
        different = False
        for i, block in enumerate(self.listBlocks):
            if (self.listNewBlocks[i].maxLeft != block.maxLeft or 
                self.listNewBlocks[i].minLeft != block.minLeft or
                self.listNewBlocks[i].maxRight != block.maxRight or 
                self.listNewBlocks[i].minRight != block.minRight):
                print('Обнаружены изменения в ')
                block = self.listNewBlocks[i]
                different = True
            else:
                print('Изменения не обнаружены')
        if different:
            with UseDatabase(self.DBCONFIG) as cursor:
                _SQl = """INSERT INTO lenta_conv(block_length, lenta_length) VALUES (%s, %s)"""
                cursor.execute(_SQl, (self.lenghtBlock, self.lenghtLenta))
                self.last_id_conv += 1
                for block in self.listBlocks:
                    with UseDatabase(self.DBCONFIG) as cursor:
                        _SQl = """INSERT INTO lenta_blocks(id_conv, dLeft, dRight, minWidth, maxWidth)
                                VALUES (%s, %s, %s, %s, %s)"""
                        cursor.execute(_SQl, (self.last_id_conv, block.dLeft, block.dRight, block.minWidth, block.maxWidth))  

DBCONFIG = {'host': '192.168.1.251',
            'user': 'user',
            'password': '0011',
            'database': 'videoai', }

cs = int(input("Количество блоков: "))
# lenta = Lenta(DBCONFIG, 1, cs, 10)

lenta = Lenta(DBCONFIG, 25/3, cs, 178.8)
rmq = mq(ip='192.168.1.251', process_name='analizator')
rmq.consume(func=lenta.callback, bindings=['calc.data.*']) 


# with open("data-test.json", "r") as read_file:
#     lenta.callback(None, read_file.read())
# with open("data-test.json", "r") as read_file:
#     lenta.callback(None, read_file.read())
# with open("data-test.json", "r") as read_file:
#     lenta.callback(None, read_file.read())
# with open("data-test.json", "r") as read_file:
#     lenta.callback(None, read_file.read())
# with open("data-test.json", "r") as read_file:
#     lenta.callback(None, read_file.read())
# with open("data-test.json", "r") as read_file:
#     lenta.callback(None, read_file.read())
# with open("data-test.json", "r") as read_file:
#     lenta.callback(None, read_file.read())