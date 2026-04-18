#pragma once
#include <iostream>
#include <stdexcept>
using namespace std;


template <class T>
class Stack {
public:

    // Constructor && Destructor
    Stack() :top(nullptr), length(0) {}
 
    ~Stack() {
        while (!_isEmpty()) {
            pop();
        }
    }


    
    void push(T ele) {
        Node* newNode = new Node(ele);
        newNode->next = top;
        top = newNode;
        length++;
    }
    T pop() {
        if (_isEmpty()) {
            throw  runtime_error("Stack is empty");
        }

        Node* temp = top;
        T value = temp->element;

        top = top->next;
        delete temp;
        length--;

        return value;
    }
    T getTop() const {
        if (_isEmpty()) throw runtime_error("Stack is empty");
        return top->element;
    }

   
    
    bool isEmpty() const {
        return top == nullptr;
    }
    
    int size() const {
        return length;
    }

    void display() const {
        Node* temp = top;
        cout << "[ ";
        while (temp != nullptr) {
            cout << temp->element;
            if (temp->next) cout << " , ";
            temp = temp->next;
        }
        cout <<" ]" << endl;
    }


private:

    struct Node {
        T element;
        Node* next;

        Node(T ele) :element(ele), next(nullptr) {}
    };

    Node* top;
    int length;
    bool _isEmpty() const {
        return top == nullptr;
    }

};



template<>
class Stack<string> {
public:

    // Constructor & Destructor
    Stack() : top(nullptr), length(0) {}

    ~Stack() {
        while (!isEmpty()) {
            pop();
        }
    }

    void push(const string& ele) {
        Node* newNode = new Node(ele);
        newNode->next = top;
        top = newNode;
        length++;
    }

    string pop() {
        if (isEmpty()) {
            throw runtime_error("Stack is empty");
        }

        Node* temp = top;
        string value = temp->element;

        top = top->next;
        delete temp;
        length--;

        return value;
    }

    string getTop() const {
        if (isEmpty())
            throw runtime_error("Stack is empty");

        return top->element;
    }

    bool isEmpty() const {
        return top == nullptr;
    }

    int size() const {
        return length;
    }

    void display() const {
        Node* temp = top;

        cout << "[ ";
        while (temp != nullptr) {
            cout << "\"" << temp->element << "\"";  // مهم للتمييز
            if (temp->next) cout << " , ";
            temp = temp->next;
        }
        cout << " ]" << endl;
    }

    bool isOperator(const string& op) const {
        return op == "+" || op == "-" || op == "*" || op == "/";
    }

    string clearOperator() {
        string temp = "";
        while (getTop() != "(") {

            temp += pop();
            temp += " ";

        }
        pop();
        return temp;

    }


private:

    struct Node {
        string element;
        Node* next;

        Node(const string& ele) : element(ele), next(nullptr) {}
    };

    Node* top;
    int length;
};