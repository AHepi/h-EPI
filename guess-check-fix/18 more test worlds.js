/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Five more test worlds (log 18), one for each ability the owner named that the first five did not
 * already cover well. Same layout as "03 test worlds.js": a request, a hidden true model (the world),
 * and jobs, some held back.
 *   moving day      - planning: does a plan reach its goal, and what goes wrong out of order
 *   river crossing  - problem solving: a puzzle with a rule about what may be left alone together
 *   plant watering  - interpreting vague prose: "when they need it", "never flood them"
 *   borrowed lantern- a story whose ending must follow, with two "what if" endings
 *   ghost lantern   - exploring creatively: add a new idea to the door game without breaking the old game
 */
module.exports = [
  {
    id: 'moving-day',
    kind: 'planning',
    request: 'Plan moving day. Boxes must be packed before they can be loaded, and the van must be booked before anything can be loaded into it. We drive off once the boxes are in the van. The key has to go back to the landlord before we drive off, or we lose the deposit; once we have driven off it is too late to hand it back.',
    world: {
      things: { boxes: ['unpacked', 'packed', 'in van'], van: ['not booked', 'booked', 'driven off'], key: ['with us', 'returned'], deposit: ['held', 'back', 'lost'] },
      events: ['pack', 'book van', 'load', 'return key', 'drive'],
      start: { boxes: 'unpacked', van: 'not booked', key: 'with us', deposit: 'held' },
      rules: [
        { name: 'packing', when: ['pack happens', 'boxes is unpacked'], then: 'boxes is packed' },
        { name: 'booking', when: ['book van happens', 'van is not booked'], then: 'van is booked' },
        { name: 'loading', when: ['load happens', 'boxes is packed', 'van is booked'], then: 'boxes is in van' },
        { name: 'driving', when: ['drive happens', 'boxes is in van', 'van is booked'], then: 'van is driven off' },
        { name: 'returning the key', when: ['return key happens', 'van is not driven off'], then: 'key is returned' },
        { name: 'deposit back', when: ['van is driven off', 'key is returned', 'deposit is held'], then: 'deposit is back' },
        { name: 'deposit lost', when: ['van is driven off', 'key is with us', 'deposit is held'], then: 'deposit is lost' },
      ],
    },
    jobs: [
      { name: 'the whole plan', events: ['pack', 'book van', 'load', 'return key', 'drive'], expect: ['van is driven off', 'deposit is back'] },
      { name: 'forgot the key', events: ['pack', 'book van', 'load', 'drive'], expect: 'deposit is lost' },
      { name: 'loading before packing', events: ['book van', 'load', 'pack', 'drive'], expect: ['boxes is packed', 'van is booked'] },
      { name: 'nothing done', events: [], expect: 'deposit is held' },
      { name: 'key handed back too late', events: ['pack', 'book van', 'load', 'drive', 'return key'], expect: 'deposit is lost', held_back: true },
      { name: 'loading before booking', events: ['pack', 'load', 'book van', 'drive'], expect: ['boxes is packed', 'van is booked', 'deposit is held'], held_back: true },
      { name: 'key first, then the rest', events: ['return key', 'book van', 'pack', 'load', 'drive'], expect: 'deposit is back', held_back: true },
    ],
  },
  {
    id: 'river-crossing',
    kind: 'problem solving',
    request: 'A farmer must get a fox, a goose and a sack of grain across a river, from the left bank to the right. The boat carries the farmer and at most one of the three, and only the farmer can row, so it can only take something from the bank the farmer is on. If the fox and the goose are left on a bank without the farmer, the fox eats the goose. If the goose and the grain are left without the farmer, the goose eats the grain.',
    world: {
      things: {
        farmer: ['left', 'right'], fox: ['left', 'right'], goose: ['left', 'right'], grain: ['left', 'right'],
        goose_is: ['alive', 'eaten'], grain_is: ['whole', 'eaten'],
      },
      events: ['cross alone', 'cross with fox', 'cross with goose', 'cross with grain'],
      start: { farmer: 'left', fox: 'left', goose: 'left', grain: 'left', goose_is: 'alive', grain_is: 'whole' },
      rules: [
        { name: 'farmer rows right alone', when: ['cross alone happens', 'farmer is left'], then: 'farmer is right' },
        { name: 'farmer rows left alone', when: ['cross alone happens', 'farmer is right'], then: 'farmer is left' },
        { name: 'farmer rows right with fox', when: ['cross with fox happens', 'farmer is left'], then: 'farmer is right' },
        { name: 'farmer rows left with fox', when: ['cross with fox happens', 'farmer is right'], then: 'farmer is left' },
        { name: 'farmer rows right with goose', when: ['cross with goose happens', 'farmer is left'], then: 'farmer is right' },
        { name: 'farmer rows left with goose', when: ['cross with goose happens', 'farmer is right'], then: 'farmer is left' },
        { name: 'farmer rows right with grain', when: ['cross with grain happens', 'farmer is left'], then: 'farmer is right' },
        { name: 'farmer rows left with grain', when: ['cross with grain happens', 'farmer is right'], then: 'farmer is left' },
        { name: 'fox goes right', when: ['cross with fox happens', 'farmer is left', 'fox is left'], then: 'fox is right' },
        { name: 'fox goes left', when: ['cross with fox happens', 'farmer is right', 'fox is right'], then: 'fox is left' },
        { name: 'goose goes right', when: ['cross with goose happens', 'farmer is left', 'goose is left'], then: 'goose is right' },
        { name: 'goose goes left', when: ['cross with goose happens', 'farmer is right', 'goose is right'], then: 'goose is left' },
        { name: 'grain goes right', when: ['cross with grain happens', 'farmer is left', 'grain is left'], then: 'grain is right' },
        { name: 'grain goes left', when: ['cross with grain happens', 'farmer is right', 'grain is right'], then: 'grain is left' },
        { name: 'fox eats goose on the left', when: ['fox is left', 'goose is left', 'farmer is right'], then: 'goose_is is eaten' },
        { name: 'fox eats goose on the right', when: ['fox is right', 'goose is right', 'farmer is left'], then: 'goose_is is eaten' },
        { name: 'goose eats grain on the left', when: ['goose is left', 'grain is left', 'farmer is right', 'goose_is is alive'], then: 'grain_is is eaten' },
        { name: 'goose eats grain on the right', when: ['goose is right', 'grain is right', 'farmer is left', 'goose_is is alive'], then: 'grain_is is eaten' },
      ],
    },
    jobs: [
      { name: 'farmer crosses alone first', events: ['cross alone'], expect: 'goose_is is eaten' },
      { name: 'goose over first', events: ['cross with goose'], expect: ['goose is right', 'goose_is is alive', 'grain_is is whole'] },
      { name: 'fox over first', events: ['cross with fox'], expect: ['grain_is is eaten', 'goose_is is alive'] },
      { name: 'the usual solution', events: ['cross with goose', 'cross alone', 'cross with fox', 'cross with goose', 'cross with grain', 'cross alone', 'cross with goose'],
        expect: ['fox is right', 'goose is right', 'grain is right', 'goose_is is alive', 'grain_is is whole'] },
      { name: 'the other solution', events: ['cross with goose', 'cross alone', 'cross with grain', 'cross with goose', 'cross with fox', 'cross alone', 'cross with goose'],
        expect: ['fox is right', 'goose is right', 'grain is right', 'goose_is is alive', 'grain_is is whole'], held_back: true },
      { name: 'fox left with the goose on the far bank', events: ['cross with goose', 'cross alone', 'cross with fox', 'cross alone'], expect: 'goose_is is eaten', held_back: true },
      { name: 'the fox cannot be fetched from the wrong bank', events: ['cross alone', 'cross with fox'], expect: 'fox is left', held_back: true },
    ],
  },
  {
    id: 'plant-watering',
    kind: 'interpreting vague prose',
    request: 'Water my plants when they need it, but don\'t waste water if it\'s going to rain. And never flood them.',
    world: {
      things: { soil: ['dry', 'damp', 'soaked'], forecast: ['clear', 'rain'], valve: ['closed', 'open'] },
      events: ['morning check', 'rain falls', 'sunny day'],
      start: { soil: 'dry', forecast: 'clear', valve: 'closed' },
      rules: [
        { name: 'open when dry and no rain coming', when: ['morning check happens', 'soil is dry', 'forecast is clear'], then: 'valve is open' },
        { name: 'water wets dry soil', when: ['valve is open', 'soil is dry'], then: 'soil is damp' },
        { name: 'close once damp', when: ['valve is open', 'soil is damp'], then: 'valve is closed' },
        { name: 'rain on dry soil', when: ['rain falls happens', 'soil is dry'], then: 'soil is damp' },
        { name: 'rain on damp soil', when: ['rain falls happens', 'soil is damp'], then: 'soil is soaked' },
        { name: 'sun dries damp soil', when: ['sunny day happens', 'soil is damp'], then: 'soil is dry' },
        { name: 'sun dries soaked soil', when: ['sunny day happens', 'soil is soaked'], then: 'soil is damp' },
      ],
    },
    jobs: [
      { name: 'dry soil, clear sky', start: { soil: 'dry', forecast: 'clear' }, events: ['morning check'], expect: 'soil is damp' },
      { name: 'dry soil, rain on the way', start: { soil: 'dry', forecast: 'rain' }, events: ['morning check'], expect: 'soil is dry' },
      { name: 'damp soil needs nothing', start: { soil: 'damp', forecast: 'clear' }, events: ['morning check'], expect: 'soil is damp' },
      { name: 'rain after skipping', start: { soil: 'dry', forecast: 'rain' }, events: ['morning check', 'rain falls'], expect: 'soil is damp' },
      { name: 'two checks do not flood', start: { soil: 'dry', forecast: 'clear' }, events: ['morning check', 'morning check'], expect: 'soil is damp', held_back: true },
      { name: 'the water is turned off again', start: { soil: 'dry', forecast: 'clear' }, events: ['morning check'], expect: 'valve is closed', held_back: true },
      { name: 'dried by the sun, then watered', start: { soil: 'damp', forecast: 'clear' }, events: ['sunny day', 'morning check'], expect: ['soil is damp', 'valve is closed'], held_back: true },
      { name: 'soaked soil is left alone', start: { soil: 'soaked', forecast: 'clear' }, events: ['morning check'], expect: ['soil is soaked', 'valve is closed'], held_back: true },
    ],
  },
  {
    id: 'borrowed-lantern',
    kind: 'a story whose ending must follow',
    request: 'A story: Ada lends her lantern to a stranger she meets on the road. Night falls before she reaches home, and without a light she gets lost in the woods. The stranger goes out searching with the lantern; Ada sees her own lantern through the trees, calls out, and is found. If she had kept her lantern she would have got home safely. If nobody had come searching she would still be lost.',
    world: {
      things: { lantern: ['with ada', 'with stranger'], ada: ['on the road', 'lost', 'found', 'home safe'], stranger: ['at home', 'searching'] },
      events: ['lend lantern', 'night falls', 'stranger searches'],
      start: { lantern: 'with ada', ada: 'on the road', stranger: 'at home' },
      rules: [
        { name: 'lending', when: ['lend lantern happens', 'lantern is with ada', 'ada is on the road'], then: 'lantern is with stranger' },
        { name: 'lost in the dark', when: ['night falls happens', 'ada is on the road', 'lantern is with stranger'], then: 'ada is lost' },
        { name: 'home by her own light', when: ['night falls happens', 'ada is on the road', 'lantern is with ada'], then: 'ada is home safe' },
        { name: 'the search', when: ['stranger searches happens'], then: 'stranger is searching' },
        { name: 'she sees her lantern', when: ['ada is lost', 'stranger is searching', 'lantern is with stranger'], then: 'ada is found' },
      ],
    },
    jobs: [
      { name: 'the story as told', events: ['lend lantern', 'night falls', 'stranger searches'], expect: 'ada is found' },
      { name: 'she keeps her lantern', events: ['night falls'], expect: 'ada is home safe' },
      { name: 'nobody searches', events: ['lend lantern', 'night falls'], expect: 'ada is lost' },
      { name: 'the search starts before dark', events: ['lend lantern', 'stranger searches', 'night falls'], expect: 'ada is found', held_back: true },
      { name: 'she kept it, and he searches anyway', events: ['night falls', 'stranger searches'], expect: 'ada is home safe', held_back: true },
      { name: 'she meets him only after dark', events: ['night falls', 'lend lantern'], expect: ['ada is home safe', 'lantern is with ada'], held_back: true },
    ],
  },
  {
    id: 'ghost-lantern',
    kind: 'exploring creatively: a new idea that must not break the old design',
    request: 'Take this small game: the player can pick up a key, open a door with it, and walk through to win. Touching the ghost costs a life, and with no lives left the game is over. Opening the door without the key does nothing. Add one new idea: the player can light a lantern that drives the ghost away for good, but lighting it burns up the key\'s magic, so the key will no longer open the door. Keep everything else as it was.',
    world: {
      things: { key: ['on floor', 'carried', 'burnt out'], door: ['locked', 'open'], lives: ['2', '1', '0'], game: ['playing', 'won', 'over'], lantern: ['dark', 'lit'], ghost: ['here', 'gone'] },
      events: ['pick up key', 'use door', 'walk through', 'touch ghost', 'light lantern'],
      start: { key: 'on floor', door: 'locked', lives: '2', game: 'playing', lantern: 'dark', ghost: 'here' },
      rules: [
        { name: 'take key', when: ['pick up key happens', 'key is on floor', 'game is playing'], then: 'key is carried' },
        { name: 'unlock', when: ['use door happens', 'key is carried', 'game is playing'], then: 'door is open' },
        { name: 'win', when: ['walk through happens', 'door is open', 'game is playing'], then: 'game is won' },
        { name: 'lose a life', when: ['touch ghost happens', 'ghost is here', 'lives is 2', 'game is playing'], then: 'lives is 1' },
        { name: 'lose the last life', when: ['touch ghost happens', 'ghost is here', 'lives is 1', 'game is playing'], then: 'lives is 0' },
        { name: 'game over', when: ['lives is 0'], then: 'game is over' },
        { name: 'light the lantern', when: ['light lantern happens', 'key is carried', 'game is playing'], then: 'lantern is lit' },
        { name: 'the key burns out', when: ['light lantern happens', 'key is carried', 'game is playing'], then: 'key is burnt out' },
        { name: 'the ghost flees', when: ['lantern is lit'], then: 'ghost is gone' },
      ],
    },
    jobs: [
      { name: 'key, door, walk: win', events: ['pick up key', 'use door', 'walk through'], expect: 'game is won' },
      { name: 'two ghost touches', events: ['touch ghost', 'touch ghost'], expect: 'game is over' },
      { name: 'door without key stays locked', events: ['use door', 'walk through'], expect: ['door is locked', 'game is playing'] },
      { name: 'the lantern drives the ghost away', events: ['pick up key', 'light lantern', 'touch ghost', 'touch ghost'], expect: ['lives is 2', 'game is playing'] },
      { name: 'the burnt key will not open the door', events: ['pick up key', 'light lantern', 'use door', 'walk through'], expect: ['door is locked', 'game is playing'] },
      { name: 'open the door first, then light the lantern', events: ['pick up key', 'use door', 'light lantern', 'walk through'], expect: 'game is won', held_back: true },
      { name: 'no key, no light', events: ['light lantern', 'touch ghost'], expect: ['lantern is dark', 'lives is 1'], held_back: true },
      { name: 'one touch, then the lantern', events: ['touch ghost', 'pick up key', 'light lantern', 'touch ghost'], expect: ['lives is 1', 'game is playing'], held_back: true },
      { name: 'the old game still works with a ghost touch', events: ['touch ghost', 'pick up key', 'use door', 'walk through'], expect: ['game is won', 'lives is 1'], held_back: true },
    ],
  },
];
