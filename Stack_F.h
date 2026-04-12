#pragma once
#include <iostream>
#include <stdexcept>
using namespace std;


template <class T>
class Stack {
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



public:

    // Constructor
    Stack() :top(nullptr), length(0) {}

    // Destructor
    ~Stack() {
        while (!_isEmpty()) {
            pop();
        }
    }

    // Push
    void push(T ele) {
        Node* newNode = new Node(ele);
        newNode->next = top;
        top = newNode;
        length++;
    }

    // Pop
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

    // Top
    T getTop() const {
        if (_isEmpty()) throw runtime_error("Stack is empty");
        return top->element;
    }

    // isEmpty (public إذا احتجته)
    bool isEmpty() const {
        return top == nullptr;
    }

    // Size
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
};