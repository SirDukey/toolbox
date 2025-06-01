class Node:
    def __init__(self, data):
        self.data = data
        self.next = None



class SinglyLinkedList:
    # Define the Linked List
    
    def __init__(self):
        # start with an empty list
        self.head = None

 
    def __iter__(self):
        # Make it iterable
        current = self.head
        while current:
            yield current.data
            current = current.next
              

    def __len__(self):
        # Make it measurable
        count = 0
        current = self.head
        while current:
            count += 1
            current = current.next
        return count
    
    
    def __getitem__(self, position):
        # Return the value of the list item at a position
        if position < 0 or position >= len(self):
            raise IndexError("Index out of range")
        
        current = self.head
        for i in range(len(self)):
            if i == position:
                return current.data
            current = current.next
    

    def __add__(self, other):
        # Add two SinglyLinkedList objects together
        if not isinstance(other, SinglyLinkedList):
            raise TypeError("Can only add another SinglyLinkedList")
        
        return self.concatenate_numbers_reversed() + other.concatenate_numbers_reversed()


    def append(self, data):
        # Add a node at the end
        new_node = Node(data)
        if not self.head:  # If list is empty
            self.head = new_node
            return
        last = self.head
        while last.next:  # Traverse to the end
            last = last.next
        last.next = new_node


    def display(self):
        # Print the linked list
        current = self.head
        while current:
            print(current.data, end=" -> ")
            current = current.next
        print("None")
    
   
    def concatenate_numbers_reversed(self):
        # Concatenate the list in reverse order
        current = self.head
        values = []
        while current:
            values.append(str(current.data))
            current = current.next
        return int(''.join(reversed(values)))

    
    def swap_by_value(self, val1, val2):
        # Swap to nodes by their values
        node1 = self.head
        node2 = self.head
        node1_prev = None
        node2_prev = None
        
        while node1 is not None:
            if node1.data == val1:
                break
            node1_prev = node1
            node1 = node1.next
        while node2 is not None:
            if node2.data == val2:
                break
            node2_prev = node2
            node2 = node2.next
        
        if node1_prev is None:
            self.head = node2
        else:
            node1_prev.next = node2
        if node2_prev is None:
            self.head = node1
        else:
            node2_prev.next = node1
        node1.next, node2.next = node2.next, node1.next
    
    
    def last_nth(self, n):
        # Return the last n-th node value
        end = len(self)
        return self[end - n]


    def get_middle(self):
        # Return the middle node value
        index = (len(self) - 1) // 2
        return self[index]

        

ll = SinglyLinkedList()
ll.append(10)
ll.append(20)
ll.append(30)
ll.display()
print(ll.concatenate_numbers_reversed())

print([x for x in ll])
print(len(ll))

ll2 = SinglyLinkedList()
ll2.append(100)
ll2.append(200)
ll2.append(300)
print(ll + ll2)
ll.display()
ll.swap_by_value(10, 20)
ll.display()
print(ll[1])
ll.append(40)
ll.append(50)
ll.display()
print(ll.last_nth(2))
print("middle: ", end='')
ll.append(60)
ll.append(70)
ll.append(80)
ll.append(5)
ll.display()
print(ll.get_middle())
print(max(ll))
print(min(ll))
