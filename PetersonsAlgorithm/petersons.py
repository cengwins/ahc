import threading
import time

mutex = threading.Lock()

def peterson(id,function):
    global flag,turn
    otherThreadId = 1 - id

    flag[id] = True         # I want to get in to critical section
    turn = otherThreadId    # Lets wait until other thread finish
    while flag[otherThreadId] and turn == otherThreadId:
        time.sleep(0.0000001)
        continue

    ####critical section####
    function(id)
    ########################    
    
    flag[id] = False    # My job is finished

def produce(id):
    global counter
    counter += 1
    #print("Thread {} counter:".format(id),counter)

def consume(id):
    global counter 
    counter -= 1
    #print("Thread {} counter:".format(id),counter)

def producer(id,ntime):
    global waitFlag
    while waitFlag:
        continue
    print("Producer {} started".format(id))
    for i in range(ntime):
        produce(id)
    print("Producer {} finished".format(id))

def producerPeterson(id,ntime):
    global waitFlag
    while waitFlag:
        continue
    print("Producer {} started".format(id))
    for i in range(ntime):
        peterson(id,produce)
    print("Producer {} finished".format(id))

def producerMutex(id,ntime):
    global waitFlag
    while waitFlag:
        continue
    print("Producer {} started".format(id))
    for i in range(ntime):
        with mutex:
            produce(id)
    print("Producer {} finished".format(id))

def consumer(id,ntime):
    global waitFlag
    while waitFlag:
        continue
    print("Consumer {} started".format(id))
    for i in range(ntime):
        consume(id)
    print("Consumer {} finished".format(id))

def consumerPeterson(id,ntime):
    global waitFlag
    while waitFlag:
        continue
    print("Consumer {} started".format(id))
    for i in range(ntime):
        peterson(id,consume)
    print("Consumer {} finished".format(id))

def consumerMutex(id,ntime):
    global waitFlag
    while waitFlag:
        continue
    print("Consumer {} started".format(id))
    for i in range(ntime):
        with mutex:
            consume(id)
    print("Consumer {} finished".format(id))

if __name__ == "__main__":
   
    ntime = 500000

    waitFlag = True
    counter = 0
    t0 = threading.Thread(target=producer, args=(0,ntime))
    t1 = threading.Thread(target=producer, args=(1,ntime))
    t0.start()
    t1.start()
    startTime = time.time()
    waitFlag = False
    t0.join()
    t1.join()
    print("Increment counters without any syncronization: Expected output {} , real output {}".format(ntime*2,counter))
    print("Time: {}".format(time.time()-startTime))

    waitFlag = True
    counter = 0
    t0 = threading.Thread(target=producerMutex, args=(0,ntime))
    t1 = threading.Thread(target=producerMutex, args=(1,ntime))
    t0.start()
    t1.start()
    startTime = time.time()
    waitFlag = False
    t0.join()
    t1.join()
    print("Increment counters with mutex: Expected output {} , real output {}".format(ntime*2,counter))
    print("Time: {}".format(time.time()-startTime))

    waitFlag = True
    counter = 0
    t0 = threading.Thread(target=producer, args=(0,ntime))
    t1 = threading.Thread(target=consumer, args=(1,ntime))
    t0.start()
    t1.start()
    startTime = time.time()
    waitFlag = False
    t0.join()
    t1.join()
    print("Producer-consumer without any syncronization: Expected output 0 , real output {}".format(counter))
    print("Time: {}".format(time.time()-startTime))
    
    waitFlag = True
    counter = 0
    t0 = threading.Thread(target=producerMutex, args=(0,ntime))
    t1 = threading.Thread(target=consumerMutex, args=(1,ntime))
    t0.start()
    t1.start()
    startTime = time.time()
    waitFlag = False
    t0.join()
    t1.join()
    print("Producer-consumer with mutex: Expected output 0 , real output {}".format(counter))
    print("Time: {}".format(time.time()-startTime))

    waitFlag = True
    flag = [False,False]
    turn = 0
    counter = 0
    t0 = threading.Thread(target=producerPeterson, args=(0,ntime))
    t1 = threading.Thread(target=producerPeterson, args=(1,ntime))
    t0.start()
    t1.start()
    startTime = time.time()
    waitFlag = False
    t0.join()
    t1.join()
    print("Increment counters with Petersons Algorithm: Expected output {} , real output {}".format(ntime*2,counter))
    print("Time: {}".format(time.time()-startTime))

    waitFlag = True
    flag = [False,False]
    turn = 0
    counter = 0
    t0 = threading.Thread(target=producerPeterson, args=(0,ntime))
    t1 = threading.Thread(target=consumerPeterson, args=(1,ntime))
    t0.start()
    t1.start()
    startTime = time.time()
    waitFlag = False
    t0.join()
    t1.join()
    print("Producer-consumer with Petersons Algorithm: Expected output 0 , real output {}".format(counter))
    print("Time: {}".format(time.time()-startTime))