import logging

class Status:

    def __init__(self):
        self._update_inprog = 0
        self._auto_update = 0
        self.logger = logging.getLogger('root.' + __name__)

    @property
    def update_inprog(self):
        return self._update_inprog

    @update_inprog.setter
    def update_inprog(self, val):
        if self._update_inprog == 1 and val == 1:
            self.logger.error('trying to update inprog to 1 when it is already inprog')
        else:
            self._update_inprog = val
            self.logger.info('Setting update_inprog to %d' % val)

    @property
    def auto_update(self):
        return self._auto_update

    @auto_update.setter
    def auto_update(self, val):
        self._auto_update = val
        self.logger.info('Setting auto update to %d' % val)