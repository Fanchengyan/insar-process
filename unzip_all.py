import os
import logging


FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(filename='./unzip.log', filemode='w',
                    level=logging.INFO, format=FORMAT)

files = [i for i in os.listdir(os.getcwd()) if i.split('.')[-1] == 'zip']
for f in files:
    logging.info('Begin unziping {}'.format(f))
    os.system('unzip {}'.format(f))
    logging.info('Unziping {} done!'.format(f))
