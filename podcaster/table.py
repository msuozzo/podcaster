"""A text-based table formatting interface
"""
from itertools import chain


class FormatError(BaseException):
    """Indicates an error in formatting
    """
    pass


class TextTable(object):
    """An ASCII table formatter
    """
    def __init__(self, cell_buffer=1):
        self._cell_buffer = cell_buffer
        self._seps = ('', '')
        self._rows = []

    def set_seps(self, *args):
        """Set the column separators for rows added after this call

        All subsequent calls to add_row must provide `len(args) - 1` cells

        As a consequence, len(args) must be >= 2 (the first and last separators
        are for the positions prior to the first element and after the final
        element, respectively).

        Also, a column separator may be empty but may not be more than a single character.

        *args: the column separator strings
        """
        if len(args) < 2:
            raise FormatError('Invalid number of separators provided (got %d, needed at least 2)' %
                    len(args))
        invalid_seps = [arg for arg in args if len(arg) > 1]
        if invalid_seps:
            sep_str = ', '.join(["'%s'" % sep for sep in invalid_seps])
            raise FormatError('Separators must be of length <=1: {%s}' % sep_str)
        self._seps = tuple(args)

    def add_row(self, cells, fill_char=' ', align='l', seps=None):
        """Add a row of cells to the grid

        cells: an iterable of the cells (strs)
            Number of cells expected: {number of separators last provided} - 1
        fill_char: character with which to pad the cells (default: ' ')
        align: how to align the string in the cell (default: 'l')
            Valid choices: 'l' (align left), 'c' (center), or 'r' (align right)
        seps: an iterable of column separators that, if provided, overrive the
            ones set by `set_seps`. Future added rows will not use these seps i.e.
            they are not remembered.
        """
        if len(fill_char) != 1:
            raise FormatError('fill char must be a single character')
        if align not in ('l', 'c', 'r'):
            raise FormatError('align argument must be one of: {l, c, r}')
        align_func = str.ljust if align == 'l' else \
                     str.center if align == 'c' else \
                     str.rjust
        old = self._seps[:]
        if seps is not None:
            self.set_seps(*seps)
        if len(cells) != len(self._seps) - 1:
            raise FormatError('Incorrect number of cells provided (got %d, needed %d)' %
                    (len(cells), len(self._seps) - 1))
        row = {'seps': self._seps,
                'cells': map(str, cells),
                'fill': fill_char,
                'align': align_func}
        self._rows.append(row)
        self.set_seps(*old)

    def add_break_row(self, fill_char='-', seps=None):
        """Add a row designed to break up grid sections
        Break rows still contain seps but are otherwise composed solely of `fill_char`s

        fill_char: the character to fill the entire row (aside from the seps)
        seps: an iterable of column separators that, if provided, overrive the
            ones set by `set_seps`. Future added rows will not use these seps i.e.
            they are not remembered.
        """
        seps = self._seps if seps is None else seps
        self.add_row(['' for _ in xrange(len(seps) - 1)], fill_char=fill_char, seps=seps)

    def _calculate_column_widths(self):
        """Return a list of the maximum lengths each column should be to
        properly contain their cells.
        """
        max_cols = max(len(row['cells']) for row in self._rows)
        col_widths = [[len(arg) for arg in row['cells']] for row in self._rows]
        valid_cols = lambda ind: [widths[ind] for widths in col_widths
                                    if ind < len(widths) - 1]
        max_widths = [max(valid_cols(col_ind)) for col_ind in xrange(max_cols - 1)]
        # Determine the proper width of the last column
        # This requires special logic because rows may have different numbers of cells
        last_col_widths = []
        for widths in col_widths:
            # The extra element adds the last cell's padding
            # a | b | c |
            #      ^^^
            clobbered_widths = max_widths[len(widths) - 1:] + [0]
            total_clobbered = self._merged_width(clobbered_widths)
            last_col_widths.append(widths[-1] - total_clobbered)
        max_widths.append(max(last_col_widths))
        return max_widths

    def _merged_width(self, widths):
        """Return the total width a number of `widths` will occupy when
        separators are added.
        """
        buffers = max(0, len(widths) - 1) * (2 * self._cell_buffer + 1)
        return sum(widths) + buffers

    def _pad_row(self, cells, widths, align_func, fill_char):
        """Return a padded row of cells

        cells: the cells to be padded
        widths: the widths to which each corresponding cell should be padded.
            May be longer than `cells` however only the first `len(cells)`
            elements will be used.
        align_func: the string alignment function that should be used to add padding
        fill_char: the character with which to pad each cell
        """
        padded = [align_func(col, widths[ind], fill_char) for ind, col in enumerate(cells[:-1])]
        # Calculate last cell separately to account for the case where this row
        # is shorter than the max row length
        merge_width = self._merged_width(widths[len(cells) - 1:])
        last_cell = align_func(cells[-1], merge_width, fill_char)
        padded.append(last_cell)
        return padded

    def __str__(self):
        widths = self._calculate_column_widths()
        lines = []
        for row in self._rows:
            # Pad cells to proper widths
            padded = self._pad_row(row['cells'], widths, row['align'], row['fill'])
            # Interleave seps with cells
            all_elems = list(chain(*zip(row['seps'], padded))) + [row['seps'][-1]]
            buffer_ = row['fill'] * self._cell_buffer
            line = buffer_.join(all_elems)
            lines.append(line)
        return '\n'.join(lines)
