
import os
import sys

maker_path = os.path.join(os.getcwd(), 'clientmaker')
sys.path.insert(0, maker_path)


from clientmaker.maker import ClientMaker

cm = ClientMaker()
cm.make()