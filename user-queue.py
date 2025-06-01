from dataclasses import dataclass
from faker import Faker
import random
from time import perf_counter
from typing import Optional, Iterator


fake = Faker('en_US')

class Node:
    def __init__(self, data: str, next: Optional['Node'] = None) -> None:
        self.data = data
        self.next = next

class Queue:
    def __init__(self):
        self.front = None
        self.rear = None
        
    def enqueue(self, data) -> None:
        new_node = Node(data)
        if not self.front or not self.rear:
            self.front = new_node
            self.rear = new_node
        else:
            self.rear.next = new_node
            self.rear = new_node
        
    def dequeue(self) -> Optional['User']:
        if not self.front:
            return 'The queue is empty'
        data = self.front.data
        self.front = self.front.next
        return data
    
    def peek(self):
        if not self.front:
            return 'The queue is empty'
        return self.front.data
    
    def sort_by_value(self, value: str) -> None:
        if not self.front:
            return 'The queue is empty'
        current = self.front
        while True:
            swapped = False
            current = self.front
            
            while current and current.next:
                if current.data.__dict__[value] > current.next.data.__dict__[value]:
                    current.data, current.next.data = current.next.data, current.data
                    swapped = True
                current = current.next
            if not swapped:
                break
    
    def __len__(self):
        count = 0
        current = self.front
        while current:
            count += 1
            current = current.next
        return count

    def __getitem__(self, index: int) -> str:
        if index < 0  or index >= len(self):
            raise IndexError('Index out of range')
        current = self.front
        for i in range(len(self)):
            if i == index:
                return current.data
            current = current.next
    
    def __iter__(self) -> Iterator[str]:
        current = self.front
        while current:
            yield current.data
            current = current.next
            

@dataclass
class User:
    name: str
    age: int


if __name__ == '__main__':
    
    user_list = []


    for i in range(30):
        user_list.append(User(fake.name(), random.choice([i for i in range(21, 66)])))


    print('\n{:=^30}'.format(' User list '))
    for user in user_list:
        print(f'{user.name}, {user.age}')


    middle_aged_user_queue = Queue()

    print('\n{:=^30}'.format(' Middle aged users '))
    middle_aged_users = filter(lambda u: 35 <= u.age <= 49, user_list)
    for middle_aged_user in middle_aged_users:
        middle_aged_user_queue.enqueue(middle_aged_user)
        print(f'{middle_aged_user.name}, {middle_aged_user.age}')
        
    print(f'\nMiddle aged users in queue: {len(middle_aged_user_queue)}')
        
    next_user = middle_aged_user_queue.peek()
    print(f'\nNext user in the queue: {next_user.name}, {next_user.age}')

    user_data = middle_aged_user_queue.dequeue()
    print(f'\nMiddle aged user dequeued: {user_data.name}, {user_data.age}')

    print(f'\nUsers in queue remaining: {len(middle_aged_user_queue)}')

    next_user = middle_aged_user_queue.peek()
    print(f'\nNext user in the queue: {next_user.name}, {next_user.age}')

    third_user = middle_aged_user_queue[2]
    print(f'\nThird user in the queue: {third_user.name}, {third_user.age}')

    middle_aged_user_ages_sorted = sorted([u.age for u in middle_aged_user_queue])
    print(f'\nMiddle aged users sorted by age: {middle_aged_user_ages_sorted}')


    start_time = perf_counter()
    middle_aged_user_queue.sort_by_value('age')
    print(f'\nMiddle aged users queue sorted by age: ')
    for u in middle_aged_user_queue:
        print(f'{u.name}, {u.age}')
    end_time = perf_counter()
    print(f'\nTime taken to sort: {end_time - start_time} seconds')

    start_time = perf_counter()
    middle_aged_user_queue.sort_by_value('name')
    print(f'\nMiddle aged users queue sorted by name: ')
    for u in middle_aged_user_queue:
        print(f'{u.name}, {u.age}')
    end_time = perf_counter()
    print(f'\nTime taken to sort: {end_time - start_time} seconds')
