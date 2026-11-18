const {test}=require('node:test');
const assert=require('node:assert/strict');
const {assessSeverity:assess}=require('../frontend/assessment.js');
const base={age:30,warningsReviewed:true,vitals:{}};
function result(input){return assess({...base,...input})}
test('disease name alone cannot determine severity',()=>{assert.equal(result({disease:'heart attack',symptoms:''}).severity,3)});
test('emergency symptoms beat mild symptoms and normal vitals',()=>{const r=result({symptoms:'mild cough and chest pain',vitals:{spo2:99,pulse:70}});assert.equal(r.severity,1);assert.equal(r.emergency,true)});
test('negation in another clause cannot hide current emergency',()=>assert.equal(result({symptoms:'no fever, but chest pain'}).severity,1));
test('not breathing is an emergency',()=>assert.equal(result({symptoms:'not breathing'}).severity,1));
test('structured warning overrides negated text',()=>assert.equal(result({symptoms:'no chest pain',warnings:['heavy bleeding']}).severity,1));
test('dangerous adult vital signs produce Critical',()=>{for(const vitals of [{spo2:89},{pulse:150},{respiratoryRate:32},{systolic:80}])assert.equal(result({symptoms:'mild cough',vitals}).severity,1)});
test('High symptoms and borderline vitals',()=>{for(const input of [{symptoms:'broken arm'},{vitals:{spo2:92}},{vitals:{temperature:40}}])assert.equal(result(input).severity,2)});
test('Medium symptoms',()=>assert.equal(result({symptoms:'headache'}).severity,3));
test('Low needs reviewed warning signs and supported mild symptoms',()=>{assert.equal(result({symptoms:'minor scratch'}).severity,4);assert.equal(result({symptoms:'minor scratch',warningsReviewed:false}).severity,3)});
test('unknown and missing data never imply Low',()=>{assert.equal(result({symptoms:'xyz'}).severity,3);assert.equal(result({symptoms:''}).severity,3)});
test('children require manual review rather than adult thresholds',()=>{const r=result({age:5,symptoms:'mild cough',vitals:{pulse:150}});assert.equal(r.severity,3);assert.match(r.reasons.join(' '),/adult vital thresholds are not applied/)});
test('invalid vital values produce validation errors',()=>{for(const spo2 of [0,101,'oops'])assert.equal(result({vitals:{spo2}}).errors.length,1)});

test('ambiguous negation never hides emergency in same clause',()=>assert.equal(result({symptoms:'no fever and chest pain'}).severity,1));
