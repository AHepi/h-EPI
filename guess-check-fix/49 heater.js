/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Log 49's second device, in the same form as log 25's four devices, so the same code can run it.
 *
 * The heater. A small room has an electric heater with a dial. You can turn the dial up, turn it down,
 * or wait. All you can see is whether the room is warm or cold.
 *
 * The heater starts on low, so the room starts warm.
 *
 * Common sense says: turning it up makes the room warm, turning it down makes it cold, waiting does
 * nothing. The truth has a hidden setting (off, low, high) and a safety cut-out: turning it up while
 * already on high trips the cut-out, and the room goes cold. While tripped, the dial does nothing;
 * only waiting resets it, and then the heater is off. So "up, up" leaves the room cold, "up, down"
 * leaves it warm, "up, up, down, up" leaves it cold, and "up, up, wait, up" warms it again.
 */
const DEVICE = {
  id: 'heater',
  kind: 'a household appliance',
  request: 'A small room has an electric heater with a dial. You can turn the dial up, turn it down, or wait. All you can see is whether the room is warm or cold.',
  visible: ['room'],
  world: {
    things: { room: ['warm', 'cold'], heater: ['off', 'low', 'high', 'tripped'] },
    events: ['turn up', 'turn down', 'wait'],
    start: { room: 'warm', heater: 'low' },
    rules: [
      { name: 'up from off', when: ['turn up happens', 'heater is off'], then: 'heater is low' },
      { name: 'up from low', when: ['turn up happens', 'heater is low'], then: 'heater is high' },
      { name: 'up from high trips', when: ['turn up happens', 'heater is high'], then: 'heater is tripped' },
      { name: 'down from high', when: ['turn down happens', 'heater is high'], then: 'heater is low' },
      { name: 'down from low', when: ['turn down happens', 'heater is low'], then: 'heater is off' },
      { name: 'waiting resets a trip', when: ['wait happens', 'heater is tripped'], then: 'heater is off' },
      { name: 'warm on low', when: ['heater is low'], then: 'room is warm' },
      { name: 'warm on high', when: ['heater is high'], then: 'room is warm' },
      { name: 'cold when off', when: ['heater is off'], then: 'room is cold' },
      { name: 'cold when tripped', when: ['heater is tripped'], then: 'room is cold' },
    ],
  },
  obvious: {
    things: { room: ['warm', 'cold'] }, events: ['turn up', 'turn down', 'wait'], start: { room: 'warm' },
    rules: [{ name: 'up warms', when: ['turn up happens'], then: 'room is warm' }, { name: 'down cools', when: ['turn down happens'], then: 'room is cold' }],
  },
};

module.exports = { DEVICE };
