import threading

def produce(id):
    global counter
    counter += 1
    #print("Thread {} counter:".format(id),counter)

def threadRoutine(id):
    global waitFlag,waitingTicket,ticket_values,threadNumber
    while waitFlag:
        continue
    print("Thread {} started".format(id))

    ticketValues[id] = max(ticketValues)+1
    waitingTicket[id] = False

    for i in range(threadNumber):
        while waitingTicket[i] == True:
            continue
        while ticketValues[i] > 0 and (ticketValues[i] < ticketValues[id] or(ticketValues[i] == ticketValues[id] and i < id)):
            continue
    ####critical section####
    produce(id)
    print("Thread {} done its job in critical section".format(id))
    ########################   
    ticketValues[id] = 0
    print("Thread {} finished".format(id))

if __name__ == "__main__":

    counter = 0
    threadNumber = 20
    waitingTicket = [True]*threadNumber
    ticketValues = [0]*threadNumber
    thread_list = []
    for i in range(threadNumber):
        thread_list.append(threading.Thread(target=threadRoutine, args=(i,)))
    waitFlag = True
    for thread in thread_list:
        thread.start()
    waitFlag = False
    for thread in thread_list:
        thread.join()

    print("Expected output {} , real output {}".format(threadNumber,counter))
    