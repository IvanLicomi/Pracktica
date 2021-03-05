import matplotlib.pyplot as plt
from DBcm import UseDatabase, ConnectError, CredentialsError, SQLError


class Lenta:
    """"""
    def __init__(self, DBCONFIG: dict, FPS: int, countBlock: int, dMin: int):
        self.DBCONFIG = DBCONFIG
        self.FPS = FPS
        self.countBlock = countBlock
        self.dMin = dMin

        self.listCadr = list()
        self.listBlocks = list()

        self.time = 0
        self.lenghtLenta = 0

    def loadDataBase(self, inputData: list, CurrentData: list) -> list:
        """Отправляет данные в БД, если есть отличия."""
        if inputData != CurrentData:
            try:
                with UseDatabase(DBCONFIG) as cursor:
                    _SQl = """INSERT INTO lenta_conv(comment)
                            VALUES ('Обнаружены изенения')"""
                    cursor.execute(_SQl)  # 'Обнаружены изенения в {0} сегменте'.format(segmentCurrent))

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

    def division_blocks(self) -> list:
        """Метод делит ленту на блоки равного размера."""
        tempList = list()
        lenghtBlock = self.lenghtLenta / self.countBlock
        print(lenghtBlock)
        iBlock = 1
        for cadr in self.listCadr:
            if cadr['distance'] < lenghtBlock * iBlock:
                tempList.append(cadr)

            elif cadr['distance'] == lenghtBlock * iBlock:
                tempList.append(cadr)
                joint = tempList[-1]
                self.listBlocks.append(tempList.copy())

                tempList.clear()
                tempList.append(joint)
                iBlock += 1

            else:
                joint = tempList[-1]
                self.listBlocks.append(tempList.copy())
                ly1, ly2 = tempList[-1]['lr'], cadr['lr']
                ly = ly1 + ((ly2 - ly1) *
                            (lenghtSegment * len(greenPoint) - x1))/(x2-x1)
                ry = ry1 + ((ry2 - ry1) *
                            (lenghtSegment * len(greenPoint) - x1))/(x2-x1)
                tempList.clear()
                tempList.append(joint)
                tempList.append(cadr)
                iBlock += 1

    def callback(self, body) -> None:
        """Метод сбора данных из пакета пришедшего с RabbitMQ.
           Данные должны приходить в формате JSON."""
        inputData = eval(body)
        iStartLenta = 0
        time = 1/self.FPS

        for cadr in inputData.keys():
            if inputData[cadr]['marker']:
                self.listCadr.append(inputData[cadr])
                iStartLenta = cadr
                break

        for cadr in list(inputData.keys())[iStartLenta+1:]:
            self.listCadr.append(inputData[cadr])
            if inputData[cadr]['marker']:
                break

        distance = 0
        self.listCadr[0]['distance'] = distance
        for i in range(1, len(self.listCadr)):
            self.listCadr[i]['distance'] = distance + self.listCadr[i]['speed'] * time
            distance += self.listCadr[i]['speed'] * time

        self.lenghtLenta = self.listCadr[-1]['distance']



DBCONFIG = {'host': '192.168.1.254',
            'user': 'user2',
            'password': '0011',
            'database': 'videoai', }

cs = int(input("Количество блоков: "))
lenta = Lenta(DBCONFIG, 15, cs, 30)

with open("data.json", "r") as read_file:
    lenta.callback(read_file.read())
    lenta.division_blocks()
    # lenta.find_loop(listSegments, 170, 190)
    # lenta.sow_conv()
