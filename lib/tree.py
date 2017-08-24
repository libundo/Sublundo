import pickle
import os

from datetime import datetime
from .diff_match_patch import diff_match_patch


def save_session(session, path):
    """
    """
    with open(path, 'wb') as loc:
        pickle.dump(session, loc, pickle.HIGHEST_PROTOCOL)


def load_session(path, buf):
    """
    """
    if os.path.exists(path):
        try:
            with open(path, 'rb') as loc:
                canidate = pickle.load(loc)
                old = canidate.text()
            if len(old) == len(buf) and old == buf:
                return canidate, True
        except EOFError:
            pass
    return UndoTree(path, buf), False


class Node:
    """
    """
    def __init__(self, idx, parent, timestamp):
        self.idx = idx
        self.parent = parent
        self.timestamp = timestamp
        self.children = []
        self.patches = {}


class UndoTree:
    """
    """
    def __init__(self, path, buf):
        """
        """
        self._root = None
        self._total = 0
        self._n_idx = 0
        self._b_idx = 0
        self._buf = None
        self._undo_file = None
        self._dmp = diff_match_patch()
        self._index = {}

    def __len__(self):
        return self._total

    def insert(self, buf):
        """
        @brief      "{ function_description }"

        @param      self  The object
        @param      buf   The buffer

        @return     { description_of_the_return_value }
        """
        self._total = self._total + 1
        tm = datetime.now().strftime('%d-%m-%Y %H-%M-%S')
        to_add = Node(self._total, None, tm)
        if self._root is None:
            self._root = to_add
        else:
            parent = self._find_parent()
            patches = self._patch(self._buf, buf)

            to_add.parent = parent
            to_add.patches[parent.idx] = patches[1]

            parent.children.append(to_add)
            parent.patches[self._total] = patches[0]

        self._n_idx = to_add.idx
        self._buf = buf
        self._index[self._total] = to_add

    def undo(self):
        """
        """
        diff = None
        parent = self.head().parent
        if parent is not None:
            self._buf, diff = self._apply_patch(parent.idx)
        return self._buf, diff

    def redo(self):
        """
        """
        diff = None
        n = self.head()
        if len(n.children) > 0:
            self._buf, diff = self._apply_patch(n.children[self._b_idx].idx)
        return self._buf, diff

    def branch(self):
        """
        """
        return self._b_idx

    def text(self):
        """
        """
        return self._buf

    def nodes(self):
        """
        """
        return self._collect(self._root)

    def head(self):
        """
        """
        return self._search(self._n_idx)

    def switch_branch(self, direction):
        """
        """
        if direction and self._b_idx + 1 < len(self.head().children):
            self._b_idx = self._b_idx + 1
        elif not direction and self._b_idx - 1 <= 0:
            self._b_idx = self._b_idx - 1
        else:
            upper = len(self.head().children) - 1
            if not direction and upper > 0:
                self._b_idx = upper
            else:
                self._b_idx = 0

    def _search(self, idx):
        """
        """
        return self._index.get(idx, None)

    def _find_parent(self):
        """
        @brief      "{ function_description }""

        @param      self  The object

        @return     { description_of_the_return_value }
        """
        maybe = self.head()
        if maybe.parent is not None and self._b_idx in maybe.parent.children:
            return maybe.parent.children[self._b_idx]
        else:
            return maybe

    def _patch(self, s1, s2):
        """
        @brief      "{ function_description }"

        @param      self  The object

        @return     { description_of_the_return_value }
        """
        d1 = self._dmp.diff_main(s1, s2)
        p1 = self._dmp.patch_make(s1, d1)

        for i in range(len(d1)):
            le = list(d1[i])
            le[0] = le[0] * -1
            d1[i] = le

        p2 = self._dmp.patch_make(s2, d1)
        return [p1, p2]

    def _apply_patch(self, idx):
        """
        @brief      "{ function_description }"

        @param      self  The object
        @param      idx   The index

        @return     { description_of_the_return_value }
        """
        patch = self.head().patches[idx]
        out = self._dmp.patch_apply(patch, self._buf)
        self._n_idx = idx
        return out[0], self._dmp.patch_toText(patch)

    def _collect(self, root):
        """
        @brief      "{ function_description }"

        @param      self  The object
        @param      root  The root

        @return     { description_of_the_return_value }
        """
        nodes = []
        if root is not None:
            nodes.append(root)
            for n in root.children:
                nodes.extend(self._collect(n))
        return nodes