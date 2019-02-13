import json

class Utils:

    def __init__(self, configpath = 'config.json'):
        self.config=configpath

    def WriteToFile(self, data,filename):
        with open('./Data/'+filename+'.txt','a') as fo:
            fo.write(str(data))
            fo.close()


    def WriteConfig(self, config):
        with open('config.json', 'w') as f:
            json.dump(config, f)

    def ReadConfig(self):
        with open('./Config/'+self.config, 'r') as f:
            config = json.load(f)
        return config

    def WriteLog(self, log):
        with open('./Log/'+'log.txt', 'a') as f:
            f.write(str(log)+'\n')
        f.close()

    def WriteToJSONFile(self,data,filename):
        with open('./Data/JSON/'+filename+'.json','a') as fo:
            json.dump(data,fo)