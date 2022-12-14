'''
Error classes to use with exceptions.
'''

class ValueAccessError(Exception):
    '''
    Exception raised when the value of a component is accessed before being set.
    '''
