from ahc.Ahc import ComponentModel, Event, GenericMessage, GenericMessageHeader, EventTypes, Thread, Lock
import torch.nn as nn
import torch.optim as optim
import torch
from sklearn import datasets, svm, metrics
from sklearn.model_selection import train_test_split
from sklearn.datasets import fetch_openml
from mnist import MNIST
import numpy as np
import pickle
from sklearn import tree

import torch.nn.functional as F

class RNNModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim):
        super(RNNModel, self).__init__()
        self.hidden_dim = hidden_dim
        self.layer_dim = layer_dim
        self.rnn = nn.RNN(input_dim, hidden_dim, layer_dim, batch_first=True, nonlinearity='relu')
        self.fc = nn.Linear(hidden_dim, output_dim)

        self.queries = {}

    def forward(self, x):
        out, hn = self.rnn(x)
        out = self.fc(out[:, -1, :])
        return out

class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim):
        super(LSTMModel, self).__init__()
        self.hidden_dim = hidden_dim
        self.layer_dim = layer_dim
        self.lstm = nn.LSTM(input_dim, hidden_dim, layer_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        out, (hn, cn) = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out

class GRUModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim):
        super(GRUModel, self).__init__()
        self.hidden_dim = hidden_dim

        self.layer_dim = layer_dim
        self.gru = nn.GRU(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        out, hn = self.gru(x)
        out = self.fc(out[:, -1, :])
        return out

class CNNMNIST(torch.nn.Module):
    def __init__(self):
        super(CNNMNIST, self).__init__()
        self.first_cnn_layer = nn.Conv2d(1, 16, 3)
        self.first_pool = nn.MaxPool2d(3, 3)
        self.first_layer = nn.Linear(16*8*8, 10)
        self.output_function = nn.Softmax(dim=1)

    def forward(self, input):
        first_cnn_layer = self.first_cnn_layer(input)
        first_cnn_out = F.leaky_relu(first_cnn_layer)
        first_pool = self.first_pool(first_cnn_out)
        # print(first_pool.shape)
        first_layer_output = self.first_layer(torch.flatten(first_pool, 1))
        if self.training == False:
            output = self.output_function(first_layer_output)
        else:
            output = first_layer_output
        return output

class MLPMNIST(nn.Module):
    def __init__(self):
        super(MLPMNIST, self).__init__()
        self.first_layer = nn.Linear(28*28, 64)
        self.second_layer = nn.Linear(64, 10)
        self.output_function = nn.Softmax(dim=1)

    def forward(self, input):
        first_layer_output = self.first_layer(input)
        # print(first_layer_output.shape)
        first_output = F.leaky_relu(first_layer_output)
        second_layer_output = self.second_layer(first_output)
        if self.training == False:
            output = self.output_function(second_layer_output)
        else:
            output = second_layer_output
        return output

# where the machine learning model is loaded... The top entity for the Node...
class ApplicationComponent(ComponentModel):
    def __init__(self, componentname, componentid):
        super(ApplicationComponent, self).__init__(componentname, componentid)
        self.node_to_model={1: "SVM", 4: "DecisionTree", 3: "RandomForest", 7: "MLP", 9: "CNN",
                            10: "LSTM", 12: "RNN", 8: "GRU"}
        self.model_to_node={self.node_to_model[a]: a for a in self.node_to_model}
        self.queries = {}
        self.query_lock = Lock()

        if self.componentinstancenumber == 1:
            self.classifier = pickle.load(open("TrainedModels/SVM/svm.model", "rb"))
        elif self.componentinstancenumber == 4:
            self.classifier = pickle.load(open("TrainedModels/DecisionTree/decisiontree.model", "rb"))
        elif self.componentinstancenumber == 3:
            self.classifier = pickle.load(open("TrainedModels/RandomForest/randomforest.model", "rb"))
        elif self.componentinstancenumber == 7:
            self.classifier = MLPMNIST()
            file_dir="TrainedModels/MLP/mlp.nn"
            self.classifier.load_state_dict(torch.load(file_dir))
            self.classifier.eval()
        elif self.componentinstancenumber == 9:
            self.classifier = CNNMNIST()
            file_dir="TrainedModels/CNN/cnn.nn"
            self.classifier.load_state_dict(torch.load(file_dir))
            self.classifier.eval()
        elif self.componentinstancenumber == 10:
            self.classifier = LSTMModel(28, 32, 1, 10)
            file_dir="TrainedModels/LSTM/lstm.nn"
            self.classifier.load_state_dict(torch.load(file_dir))
            self.classifier.eval()
        elif self.componentinstancenumber == 12:
            self.classifier = RNNModel(28, 32, 1, 10)
            file_dir="TrainedModels/RNN/rnn.nn"
            self.classifier.load_state_dict(torch.load(file_dir))
            self.classifier.eval()
        elif self.componentinstancenumber == 8:
            self.classifier = GRUModel(28, 32, 1, 10)
            file_dir="TrainedModels/GRU/gru.nn"
            self.classifier.load_state_dict(torch.load(file_dir))
            self.classifier.eval()



    def detect(self, input):
        if self.componentinstancenumber in (1, 3, 4):
            return self.classifier.predict([input])
        elif self.componentinstancenumber == 7:
            output = self.classifier(torch.from_numpy(np.array([input], dtype=np.float32)))
            return torch.argmax(output, dim=1)
        elif self.componentinstancenumber == 9: # , 10, 12, 8):
            output = self.classifier(torch.from_numpy(np.array([input], dtype=np.float32)).reshape((-1, 1, 28, 28)))
            return torch.argmax(output, dim=1)
        elif self.componentinstancenumber == 10: # , 10, 12, 8):
            output = self.classifier(torch.from_numpy(np.array([input], dtype=np.float32)).reshape((-1, 28, 28)))
            return torch.argmax(output, dim=1)
        elif self.componentinstancenumber == 12: # , 10, 12, 8):
            output = self.classifier(torch.from_numpy(np.array([input], dtype=np.float32)).reshape((-1, 28, 28)))
            return torch.argmax(output, dim=1)
        elif self.componentinstancenumber == 8: # , 10, 12, 8):
            output = self.classifier(torch.from_numpy(np.array([input], dtype=np.float32)).reshape((-1, 28, 28)))
            return torch.argmax(output, dim=1)



    def job(self, *args):
        mndata = MNIST("./datasets/mnist/")
        images, labels = mndata.load_training()
        images = np.array(images, dtype=np.float32)
        labels = np.array(labels, dtype=np.long)
        images /= (images.max(axis=0) + 1)  # Scale values...
        images = images.reshape((-1, 28 * 28))
        while True:
            data = input("Information to send : ")
            try:
                number = int(data)
            except:
                number = 0
            message_header = GenericMessageHeader("APPQUERY",
                                                  "ApplicationComponent-" + str(self.componentinstancenumber),
                                                  "Coordinator-" + str(self.componentinstancenumber))

            for machine_learning_models in self.model_to_node:
                message = GenericMessage(message_header, (self.model_to_node[machine_learning_models], images[number]))
                kickstarter = Event(self, EventTypes.MFRT, message)
                self.send_down(kickstarter)
                self.query_lock.acquire()
                self.queries[machine_learning_models] = [self.model_to_node[machine_learning_models], None]
                self.query_lock.release()

    def on_init(self, eventobj: Event):
        if self.componentinstancenumber == 0:
            message_header = GenericMessageHeader("INITIATE", "ApplicationComponent-"+str(self.componentinstancenumber),
                                                  "Coordinator-" + str(self.componentinstancenumber))
            message = GenericMessage(message_header, "")
            kickstarter = Event(self, EventTypes.MFRT, message)
            self.send_down(kickstarter)
            print(f"App {self.componentinstancenumber} sends an INITIATE to Coordinator")

            thread = Thread(target=self.job, args=[45, 54, 123])
            thread.start()

    def on_message_from_bottom(self, eventobj: Event):
        sender = eventobj.eventcontent.header.messagefrom.split("-")[0]
        messageto = eventobj.eventcontent.header.messageto.split("-")[0]
        message_type = eventobj.eventcontent.header.messagetype
        message = eventobj.eventcontent.payload
        if messageto == "ApplicationComponent":
            if message_type == "APPQUERY":
                source, content = message
                print(f"App {self.componentinstancenumber} has received {message} from {source}")
                message_header = GenericMessageHeader("APPRESPONSE",
                                                      "ApplicationComponent-" + str(self.componentinstancenumber),
                                                      "Coordinator-" + str(self.componentinstancenumber))
                resp = self.detect(content)
                print(f"Response {resp}")
                message = GenericMessage(message_header, (source, "Hellooooooooo "+str(resp)))
                kickstarter = Event(self, EventTypes.MFRT, message)
                self.send_down(kickstarter)

            elif message_type == "APPRESPONSE":
                source, content = message
                # print(f"App {self.componentinstancenumber} has received APPRESPONSE {message} from {source}")
                self.query_lock.acquire()
                self.queries[self.node_to_model[source]][1] = content
                all_responded = True
                for machine_models in self.queries:
                    if self.queries[machine_models][1] is None:
                        all_responded = False

                if all_responded:
                    print("********************All responded*********************")
                    for machine_models in self.queries:
                        print(f"{machine_models} responded {self.queries[machine_models][1]}")
                self.query_lock.release()

