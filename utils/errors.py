'''
Error classes to use with exceptions.
'''

class ValueAccessError(Exception):
    '''
    Exception raised when the value of a component is accessed before being set.
    '''


class NoPlayersError(ValueError):
    '''
    Error to throw when players can't be found.
    '''


class NoGamesError(ValueError):
    '''
    Error to throw when games can't be found.
    '''