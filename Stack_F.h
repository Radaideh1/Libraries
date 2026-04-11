#pragma once
#include <iostream>
using namespace std;

class Stack {
private:
    struct Node {
        char letter;
        Node* next;

        Node(char ch) : letter(ch), next(nullptr) {}
    };

    Node* top;
    int length;

    bool _isEmpty() const {
        return top == nullptr;
    }

public:
    // Constructor
    Stack() : top(nullptr), length(0) {}

    // Destructor
    ~Stack() {
        while (!_isEmpty()) {
            pop();
        }
    }

    // Push
    void push(char val) {
        Node* newNode = new Node(val);
        newNode->next = top;
        top = newNode;
        length++;
    }

    // Pop
    char pop() {
        if (_isEmpty()) {
            return '\0'; // بدون طباعة
        }

        Node* temp = top;
        char value = temp->letter;

        top = top->next;
        delete temp;
        length--;

        return value;
    }

    // Top
    char getTop() const {
        if (_isEmpty()) return '\0';
        return top->letter;
    }

    // isEmpty (public إذا احتجته)
    bool isEmpty() const {
        return top == nullptr;
    }

    // Size
    int size() const {
        return length;
    }

    // Display (للتجربة فقط)
    void display() const {
        Node* temp = top;
        cout << "Top -> ";
        while (temp != nullptr) {
            cout << temp->letter;
            if (temp->next) cout << " , ";
            temp = temp->next;
        }
        cout << endl;
    }
};