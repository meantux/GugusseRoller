// Gugusse Roller adaptable pin detector.
// Author: Denis-Carl Robidoux, 2020
// License: Creative Commons Attribution + ShareAlike	BY-SA
// See https://creativecommons.org/licenses/by-sa/4.0/ for details.

int ledPin = 13;        
int learnPin=5;
int outPin = ledPin;
int learning=LOW;
int min=32767;
int max=   -1;
int analog=A0;
int threshold=512;
int currentState=LOW;
int current=0;

void setup () {
    pinMode(ledPin, OUTPUT);
    pinMode(learnPin, INPUT);
    digitalWrite(outPin, LOW);
}

void loop () {
    if (learning!=digitalRead(learnPin)){
        if (learning==LOW){
            digitalWrite(outPin,LOW);
            currentState=LOW;
            learning=HIGH;
            min=32767;
            max= -1;        
        }else{
            learning=LOW;
            threshold=min+((max-min)/8);                
        }       
    }
    current=analogRead(analog);
    if (learning==HIGH){
        if (current > max){
                max=current;
        }
        if (current < min){
                min=current;
	}
    } else {
        if (currentState == LOW && current < threshold){
            digitalWrite(outPin,HIGH);
            currentState=HIGH;
        }
        if (currentState == HIGH && current > threshold){
            digitalWrite(outPin,LOW);
            currentState=LOW;
        }
    }  
}

