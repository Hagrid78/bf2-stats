
import collections

from processors import BaseProcessor

class AwardProcessor(BaseProcessor):

    def __init__(self, name, desc, columns, notes=''):
        BaseProcessor.__init__(self)

        assert name and len(name) > 0, 'Award processor requires a name.'
        assert desc and len(desc) > 0, 'Award processor requires a description.'
        assert columns and len(columns) > 0, 'Award processor requires at least one column.'

        self.name = name
        self.desc = desc
        self.columns = columns
        self.notes = notes
        self.results = collections.Counter()

    def get_results(self):
        '''
        Gets the results calculated by this award implementation. By default, the results consist of
        a list of lists to essentially create a table. So for each row in the top-level list, we
        have a secondary list that contains all the values applicable for this award. Typically,
        this will just include a player name and a numeric value. Some implementations may override
        this function to produce more complex results, such as additional columns.

        Args:
           None

        Returns:
            results (list): A list of lists to represent a table of result values.
        '''

        return self._dict_to_rows(self.results)

    def _dict_to_rows(self, values):
        '''
        This funtcion converts the given dictionary of players -> value into a table of result
        values that matches the standard format expected by the get_results function. Keys of the
        dictionary should be player objects and values can be any primitive type. After the results
        table is generated, the rows are automatically sorted by the value column.

        Args:
           values (dict)

        Returns:
            results (list): A sorted list of lists to represent a table of result values.
        '''

        if not values: return []

        # Create a list of lists, where each row is a player name and value
        results = []
        for player,value in values.iteritems():
            results.append([ player.name, values[player] ])

        # Figure out the column and direction to use when sorting
        sort_index = None
        sort_dir = None
        for index,column in enumerate(self.columns):
            if column.sorted != None:
                sort_index = index
                sort_dir = column.sorted
                break

        # Sort the results if applicable
        if sort_index:
            results.sort(key=lambda row: row[sort_index], reverse=sort_dir)
        return results

class Column(object):

    # Data constants
    NUMBER = 'number'
    STRING = 'string'

    # Sorted constants
    ASC = False
    DESC = True

    def __init__(self, name, data=STRING, sorted=None):
        self.name = name
        self.data = data
        self.sorted = sorted