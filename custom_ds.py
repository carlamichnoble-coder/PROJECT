class _BSTNode:
    __slots__ = ("key", "data", "left", "right", "height")
    def __init__(self, key: str, data: dict):
        self.key    = key       # doctor name (lowercase)
        self.data   = data      # full doctor dict
        self.left   = None
        self.right  = None
        self.height = 1         # New nodes start with a height of 1

class DoctorBST:
    def __init__(self):
        self._root = None

    def _get_height(self, node) -> int:
        return node.height if node else 0

    def _get_balance(self, node) -> int:
        if not node:
            return 0
        return self._get_height(node.left) - self._get_height(node.right)

    def _right_rotate(self, y):
        x = y.left
        T2 = x.right
        x.right = y
        y.left = T2
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))
        return x

    def _left_rotate(self, x):
        y = x.right
        T2 = y.left
        y.left = x
        x.right = T2
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        return y

    # Insert with Self-Balancing (AVL)
    def insert(self, doctor: dict):
        key = doctor["name"].lower()
        self._root = self._insert(self._root, key, doctor)

    def _insert(self, node, key, data):
        if node is None:
            return _BSTNode(key, data)

        if key < node.key:
            node.left = self._insert(node.left, key, data)
        elif key > node.key:
            node.right = self._insert(node.right, key, data)
        else:
            node.data = data  # Update matching key
            return node

        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        balance = self._get_balance(node)

        # Left Left Case
        if balance > 1 and key < node.left.key:
            return self._right_rotate(node)
        # Right Right Case
        if balance < -1 and key > node.right.key:
            return self._left_rotate(node)
        # Left Right Case
        if balance > 1 and key > node.left.key:
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)
        # Right Left Case
        if balance < -1 and key < node.right.key:
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)

        return node

    def search(self, name: str) -> dict | None:
        """Guaranteed O(log n) search — AVL balance ensures tree height stays O(log n)."""
        node = self._search(self._root, name.lower())
        return node.data if node else None

    def _search(self, node, key):
        if node is None or node.key == key:
            return node
        if key < node.key:
            return self._search(node.left, key)
        return self._search(node.right, key)

    def search_prefix(self, prefix: str) -> list:
        results = []
        self._prefix_scan(self._root, prefix.lower(), results)
        return results

    def _prefix_scan(self, node, prefix, results):
        if node is None:
            return

        if node.key.startswith(prefix):
            results.append(node.data)

        if prefix <= node.key:
            self._prefix_scan(node.left, prefix, results)

        if node.key[:len(prefix)] <= prefix:
            self._prefix_scan(node.right, prefix, results)

    def delete(self, name: str):
        self._root = self._delete(self._root, name.lower())

    def _delete(self, node, key):
        if node is None:
            return None

        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left

            # Two children: replace with in-order successor
            successor = node.right
            while successor.left:
                successor = successor.left

            node.key = successor.key
            node.data = successor.data
            node.right = self._delete(node.right, successor.key)

        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))
        balance = self._get_balance(node)

        if balance > 1 and self._get_balance(node.left) >= 0:
            return self._right_rotate(node)
        if balance > 1 and self._get_balance(node.left) < 0:
            node.left = self._left_rotate(node.left)
            return self._right_rotate(node)
        if balance < -1 and self._get_balance(node.right) <= 0:
            return self._left_rotate(node)
        if balance < -1 and self._get_balance(node.right) > 0:
            node.right = self._right_rotate(node.right)
            return self._left_rotate(node)

        return node

    def inorder(self) -> list:
        result = []
        self._inorder(self._root, result)
        return result

    def _inorder(self, node, result):
        if node is None:
            return
        self._inorder(node.left, result)
        result.append(node.data)
        self._inorder(node.right, result)

    def clear(self):
        self._root = None

    def __len__(self):
        return self._count(self._root)

    def _count(self, node):
        if node is None:
            return 0
        return 1 + self._count(node.left) + self._count(node.right)


#  GREEDY SLOT OPTIMIZER

def greedy_available_slots(appt_map,
                           doctor: dict,
                           date_str: str,
                           slot_duration: int = 30) -> list:

    start_mins = time_str_to_minutes(doctor["start_time"])
    end_mins   = time_str_to_minutes(doctor["end_time"])
    doc_label  = f"Dr. {doctor['name']} — {doctor['specialization']}"

    booked = []
    if date_str in appt_map:
        heap = appt_map.get_heap(date_str)
        for _, time_val, appt in heap:
            if appt.get("doctor", "") == doc_label:
                b_start = time_str_to_minutes(time_val)
                b_end   = b_start + slot_duration   # treat each booking as occupying one slot
                booked.append((b_start, b_end))     # store as (start, end) tuple

    booked.sort(key=lambda x: x[0])   # sort by start time

    available  = []
    candidate  = start_mins
    booked_idx = 0
    num_booked = len(booked)

    # Two-pointer timeline scan
    while candidate + slot_duration <= end_mins:
        candidate_end = candidate + slot_duration
        conflict = False

        # Fast-forward past booked slots that end before or at our candidate start
        while booked_idx < num_booked and booked[booked_idx][1] <= candidate:
            booked_idx += 1

        # Check if the next booked slot overlaps our candidate window
        if booked_idx < num_booked:
            b_start, b_end = booked[booked_idx]
            if b_start < candidate_end and candidate < b_end:
                conflict = True

        if not conflict:
            h, m = divmod(candidate, 60)
            available.append(f"{h:02d}:{m:02d}")
            candidate += slot_duration
        else:
            # Greedy jump: skip directly to end of the conflicting slot
            candidate = booked[booked_idx][1]

    return available


#  HASH MAP

class _Slot:
    """Internal slot wrapper so we can distinguish EMPTY vs DELETED vs FILLED."""
    __slots__ = ("key", "value", "state")   # "empty" | "deleted" | "filled"

    def __init__(self):
        self.key   = None
        self.value = None
        self.state = "empty"


class HashMap:

    _INITIAL_CAPACITY = 8
    _LOAD_GROW        = 0.65
    _LOAD_SHRINK      = 0.15

    def __init__(self):
        self._cap   = self._INITIAL_CAPACITY
        self._size  = 0
        self._table = [_Slot() for _ in range(self._cap)]

    def _hash(self, key: str) -> int:
        #FNV-1a variant hash
        if not isinstance(key, str):
            key = str(key)
        h = 2166136261          # FNV offset basis (32-bit)
        for ch in key:
            h ^= ord(ch)
            h  = (h * 16777619) & 0xFFFFFFFF
        return h % self._cap

    def _probe(self, key: str):
        idx = self._hash(key)
        first_deleted = -1
        for _ in range(self._cap):
            slot = self._table[idx]
            if slot.state == "empty":
                return (first_deleted if first_deleted != -1 else idx), False
            if slot.state == "deleted":
                if first_deleted == -1:
                    first_deleted = idx
            elif slot.key == key:
                return idx, True
            idx = (idx + 1) % self._cap
        return (first_deleted if first_deleted != -1 else idx), False

    def _resize(self, new_cap: int):
        old_table = self._table
        self._cap   = new_cap
        self._size  = 0
        self._table = [_Slot() for _ in range(self._cap)]
        for slot in old_table:
            if slot.state == "filled":
                self._set_raw(slot.key, slot.value)

    def _set_raw(self, key, value):
        idx, found = self._probe(key)
        slot = self._table[idx]
        if not found:
            self._size += 1
        slot.key   = key
        slot.value = value
        slot.state = "filled"

    def __setitem__(self, key, value):
        if (self._size + 1) / self._cap > self._LOAD_GROW:
            self._resize(self._cap * 2)
        idx, found = self._probe(key)
        slot = self._table[idx]
        if not found:
            self._size += 1
        slot.key   = key
        slot.value = value
        slot.state = "filled"

    def __getitem__(self, key):
        idx, found = self._probe(key)
        if not found:
            raise KeyError(key)
        return self._table[idx].value

    def __delitem__(self, key):
        idx, found = self._probe(key)
        if not found:
            raise KeyError(key)
        self._table[idx].state = "deleted"
        self._size -= 1
        if self._cap > self._INITIAL_CAPACITY and self._size / self._cap < self._LOAD_SHRINK:
            self._resize(max(self._INITIAL_CAPACITY, self._cap // 2))

    def __contains__(self, key) -> bool:
        _, found = self._probe(key)
        return found

    def __len__(self) -> int:
        return self._size

    def get(self, key, default=None):
        idx, found = self._probe(key)
        if found:
            return self._table[idx].value
        return default

    def pop(self, key, *args):
        idx, found = self._probe(key)
        if found:
            val = self._table[idx].value
            self._table[idx].state = "deleted"
            self._size -= 1
            if self._cap > self._INITIAL_CAPACITY and self._size / self._cap < self._LOAD_SHRINK:
                self._resize(max(self._INITIAL_CAPACITY, self._cap // 2))
            return val
        if args:
            return args[0]
        raise KeyError(key)

    def update(self, other):
        if isinstance(other, HashMap):
            for k, v in other.items():
                self[k] = v
        else:
            for k, v in other.items():
                self[k] = v

    def clear(self):
        self._cap   = self._INITIAL_CAPACITY
        self._size  = 0
        self._table = [_Slot() for _ in range(self._cap)]

    def keys(self):
        return [s.key for s in self._table if s.state == "filled"]

    def values(self):
        return [s.value for s in self._table if s.state == "filled"]

    def items(self):
        return [(s.key, s.value) for s in self._table if s.state == "filled"]

    def __iter__(self):
        return iter(self.keys())

    def __repr__(self):
        inner = ", ".join(f"{k!r}: {v!r}" for k, v in self.items())
        return "{" + inner + "}"

    def __bool__(self):
        return self._size > 0


#  HASH SET

class HashSet:

    _SENTINEL = True

    def __init__(self):
        self._map = HashMap()

    @staticmethod
    def _encode(element) -> str:
        if isinstance(element, tuple):
            return "\x00".join(str(x) for x in element)
        return str(element)

    def add(self, element):
        self._map[self._encode(element)] = self._SENTINEL

    def discard(self, element):
        key = self._encode(element)
        if key in self._map:
            del self._map[key]

    def remove(self, element):
        key = self._encode(element)
        del self._map[key]

    def __contains__(self, element) -> bool:
        return self._encode(element) in self._map

    def __len__(self) -> int:
        return len(self._map)

    def __bool__(self) -> bool:
        return len(self._map) > 0

    def clear(self):
        self._map.clear()

    def update(self, iterable):
        for el in iterable:
            self.add(el)

    def __iter__(self):
        return iter(self._map.keys())

    def __repr__(self):
        return "{" + ", ".join(repr(k) for k in self._map.keys()) + "}"


#  MIN-HEAP  (binary heap stored in a plain list)

class MinHeap:

    def __init__(self):
        self._data = []          # flat list of (rank, time_val, appt)

    @staticmethod
    def _parent(i):   return (i - 1) // 2
    @staticmethod
    def _left(i):     return 2 * i + 1
    @staticmethod
    def _right(i):    return 2 * i + 2

    @staticmethod
    def _less(a, b) -> bool:
        ra, ta = a[0], a[1]
        rb, tb = b[0], b[1]
        if ra != rb:
            return ra < rb          # lower rank = higher priority
        return ta < tb              # earlier time = higher priority (FCFS)

    def _sift_up(self, i: int):
        while i > 0:
            p = self._parent(i)
            if self._less(self._data[i], self._data[p]):
                self._data[i], self._data[p] = self._data[p], self._data[i]
                i = p
            else:
                break

    def _sift_down(self, i: int):
        n = len(self._data)
        while True:
            smallest = i
            l = self._left(i)
            r = self._right(i)
            if l < n and self._less(self._data[l], self._data[smallest]):
                smallest = l
            if r < n and self._less(self._data[r], self._data[smallest]):
                smallest = r
            if smallest == i:
                break
            self._data[i], self._data[smallest] = self._data[smallest], self._data[i]
            i = smallest

    def push(self, item: tuple):
        self._data.append(item)
        self._sift_up(len(self._data) - 1)

    def pop(self) -> tuple:
        """Remove and return the minimum item."""
        if not self._data:
            raise IndexError("pop from empty heap")
        self._data[0], self._data[-1] = self._data[-1], self._data[0]
        item = self._data.pop()
        if self._data:
            self._sift_down(0)
        return item

    def peek(self) -> tuple:
        if not self._data:
            raise IndexError("peek from empty heap")
        return self._data[0]

    def heapify(self, items: list):
        self._data = list(items)
        n = len(self._data)
        for i in range(self._parent(n - 1), -1, -1):
            self._sift_down(i)

    def rebuild(self):
        self.heapify(self._data)

    def replace_item(self, old_appt: dict, new_rank: int):
        for i, (rank, tv, appt) in enumerate(self._data):
            if appt is old_appt:
                self._data[i] = (new_rank, tv, appt)
                self._sift_up(i)
                self._sift_down(i)
                return

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return len(self._data) > 0

    def __iter__(self):
        return iter(self._data)

    def snapshot(self) -> list:
        temp = MinHeap()
        temp.heapify(list(self._data))
        result = []
        while temp:
            result.append(temp.pop())
        return result

    def to_list(self) -> list:
        return list(self._data)

    def __repr__(self):
        return f"MinHeap({self._data!r})"


#  DATE → APPOINTMENT MAP  (HashMap of MinHeaps)

class DateAppointmentMap:

    def __init__(self):
        self._map = HashMap()   # date_str → MinHeap

    def _get_or_create(self, date_str: str) -> MinHeap:
        if date_str not in self._map:
            self._map[date_str] = MinHeap()
        return self._map[date_str]

    def push(self, date_str: str, rank: int, time_val: str, appt: dict):
        """Insert an appointment into the correct date's heap."""
        heap = self._get_or_create(date_str)
        heap.push((rank, time_val, appt))

    def pop_next(self, date_str: str) -> tuple:
        """Pop the highest-priority appointment for a given date."""
        if date_str not in self._map:
            raise KeyError(date_str)
        return self._map[date_str].pop()

    def get_heap(self, date_str: str) -> MinHeap:
        return self._map.get(date_str, MinHeap())

    def sorted_dates(self) -> list:
        """Return date keys in chronological (lexicographic) ascending order."""
        keys = self._map.keys()
        # Insertion sort — 'YYYY-MM-DD' strings: lexicographic order = chronological
        for i in range(1, len(keys)):
            key = keys[i]
            j = i - 1
            while j >= 0 and keys[j] > key:
                keys[j + 1] = keys[j]
                j -= 1
            keys[j + 1] = key
        return keys

    def remove_appointments_for_doctor(self, doctor_username: str):
        removed_slots = set()
        for date_str in self._map.keys():
            heap = self._map[date_str]
            kept = []
            for rank, time_val, appt in heap:
                if appt.get("doctor_username") == doctor_username:
                    removed_slots.add(
                        (doctor_username, date_str, appt.get("time_disp", ""))
                    )
                else:
                    kept.append((rank, time_val, appt))
            heap.heapify(kept)
        return removed_slots

    def remove_appointments_for_patient(self, patient_username: str):
        removed_slots = set()
        for date_str in self._map.keys():
            heap = self._map[date_str]
            kept = []
            for rank, time_val, appt in heap:
                if appt.get("patient_username") == patient_username:
                    removed_slots.add((
                        appt.get("doctor_username", ""),
                        date_str,
                        appt.get("time_disp", "")
                    ))
                else:
                    kept.append((rank, time_val, appt))
            heap.heapify(kept)
        return removed_slots

    def __contains__(self, date_str: str) -> bool:
        return date_str in self._map

    def __len__(self) -> int:
        return len(self._map)

    def clear(self):
        self._map.clear()

    def keys(self):
        return self._map.keys()

    def items(self):
        return self._map.items()

    def to_serialisable(self) -> dict:
        result = {}
        for date_str, heap in self._map.items():
            result[date_str] = heap.to_list()
        return result

    def from_serialisable(self, data: dict):
        """Restore from the dict produced by to_serialisable()."""
        self.clear()
        for date_str, entries in data.items():
            heap = self._get_or_create(date_str)
            heap.heapify([(e[0], e[1], e[2]) for e in entries])


#  HASH-BASED AUTHENTICATION LOOKUP

def hash_lookup_user(username: str, password: str,
                     admin_user: dict,
                     doctors_map: HashMap,
                     patients_map: HashMap):

    if username == admin_user["username"] and password == admin_user["password"]:
        return admin_user

    doc = doctors_map.get(username)
    if doc is not None and doc["password"] == password:
        return {"role": "doctor", "data": doc}

    pat = patients_map.get(username)
    if pat is not None and pat["password"] == password:
        return {"role": "patient", "data": pat}

    return None


# CONFLICT DETECTION ALGORITHM

def time_str_to_minutes(time_str: str) -> int:
    try:
        h, m = time_str.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return 0


def check_exact_conflict(occupied, doctor_username: str,
                         date_str: str, time_display: str) -> bool:
    return (doctor_username, date_str, time_display) in occupied


def check_30min_conflict(appt_map: DateAppointmentMap,
                         doctors_map: HashMap,
                         doctor_username: str,
                         date_str: str,
                         new_time_val: str) -> bool:

    if date_str not in appt_map:
        return False

    doc = doctors_map.get(doctor_username)
    if doc is None:
        return False
    doc_label = f"Dr. {doc['name']} — {doc['specialization']}"

    new_mins = time_str_to_minutes(new_time_val)
    heap = appt_map.get_heap(date_str)

    for _, time_val, appt in heap:      # O(k) scan over appointments on that date
        if appt.get("doctor", "") != doc_label:
            continue
        existing_mins = time_str_to_minutes(time_val)
        if abs(new_mins - existing_mins) < 30:
            return True
    return False
