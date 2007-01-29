import logging.handlers

class SatchmoHandler(logging.handlers.MemoryHandler):
    
    def flush(self):
        print "Flushing"
