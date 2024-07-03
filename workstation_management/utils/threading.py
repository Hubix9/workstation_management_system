import threading

class ThreadWithCallback(threading.Thread):
    def __init__(self, callback=None, callback_args=(), *args, **kwargs):
        target = kwargs.pop('target')
        super(ThreadWithCallback, self).__init__(target=self.target_with_callback, *args, **kwargs)
        self.callback = callback
        self.method = target
        self.callback_args = callback_args

    def target_with_callback(self, *args, **kwargs):
        self.method(*args, **kwargs)
        if self.callback is not None:
            self.callback(*self.callback_args)