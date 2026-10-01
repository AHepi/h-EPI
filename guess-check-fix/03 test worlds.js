/*
 * WHAT THIS FILE DOES, IN PLAIN WORDS
 *
 * Five small test worlds, one per kind of task the tool is meant for:
 *   ball and wall   - physical cause and effect
 *   hidden ball     - something moves out of sight and comes back (needs a new thing to be tracked)
 *   door game       - planning a video game's rules
 *   lighthouse story- a story whose ending has to follow from its scenes
 *   reminder app    - a vague request from a user, where the tool has to find what to ask
 *
 * Each world has:
 *   request    - what a person would say, in plain words (this is all the guesser gets, plus the jobs)
 *   world      - the hidden true model. It stands in for the real world (or the owner's intent).
 *                It is used to answer deciding tests and to grade held-back jobs. The guesser never sees it.
 *   jobs       - what the owner says must come out right. Jobs marked held_back are kept from the
 *                guesser until the end, to catch guesses that only fit what they were shown.
 */
module.exports = [
  {
    id: 'ball-and-wall',
    kind: 'physical cause and effect',
    request: 'A ball is thrown at a wall. What happens to it? A rubber ball bounces back to the thrower. A clay ball sticks to the wall. If there is a hole in the wall, the ball goes through.',
    world: {
      things: { ball: ['in hand', 'flying', 'stuck on wall', 'back in hand', 'beyond wall'], material: ['rubber', 'clay'], wall: ['solid', 'holed'] },
      events: ['throw'],
      start: { ball: 'in hand', material: 'rubber', wall: 'solid' },
      rules: [
        { name: 'throwing', when: ['throw happens', 'ball is in hand'], then: 'ball is flying' },
        { name: 'bouncing', when: ['ball is flying', 'wall is solid', 'material is rubber'], then: 'ball is back in hand' },
        { name: 'sticking', when: ['ball is flying', 'wall is solid', 'material is clay'], then: 'ball is stuck on wall' },
        { name: 'passing through', when: ['ball is flying', 'wall is holed'], then: 'ball is beyond wall' },
      ],
    },
    jobs: [
      { name: 'rubber ball at solid wall', start: { material: 'rubber', wall: 'solid' }, events: ['throw'], expect: 'ball is back in hand' },
      { name: 'clay ball at solid wall', start: { material: 'clay', wall: 'solid' }, events: ['throw'], expect: 'ball is stuck on wall' },
      { name: 'ball not thrown', start: { material: 'rubber', wall: 'solid' }, events: [], expect: 'ball is in hand' },
      { name: 'rubber ball at holed wall', start: { material: 'rubber', wall: 'holed' }, events: ['throw'], expect: 'ball is beyond wall' },
      { name: 'clay ball at holed wall', start: { material: 'clay', wall: 'holed' }, events: ['throw'], expect: 'ball is beyond wall', held_back: true },
      { name: 'clay ball not thrown', start: { material: 'clay', wall: 'holed' }, events: [], expect: 'ball is in hand', held_back: true },
      { name: 'rubber ball is ever flying', start: { material: 'rubber', wall: 'solid' }, events: ['throw'], expect: 'ball is flying', at: 'ever', held_back: true },
    ],
  },
  {
    id: 'hidden-ball',
    kind: 'things out of sight keep existing',
    request: 'A ball rolls from spot 1 to spot 4, one spot per step. A screen can hide spots 2 and 3. We only see where the ball is when it is not hidden. Predict what we see.',
    world: {
      things: { place: ['1', '2', '3', '4'], screen: ['down', 'up'], seen: ['at 1', 'at 2', 'at 3', 'at 4', 'nothing'] },
      events: [],
      start: { place: '1', screen: 'down', seen: 'at 1' },
      rules: [
        { name: 'roll 1 to 2', when: ['place is 1'], then: 'place is 2' },
        { name: 'roll 2 to 3', when: ['place is 2'], then: 'place is 3' },
        { name: 'roll 3 to 4', when: ['place is 3'], then: 'place is 4' },
        { name: 'see 1', when: ['place is 1'], then: 'seen is at 1' },
        { name: 'see 2', when: ['place is 2', 'screen is down'], then: 'seen is at 2' },
        { name: 'see 3', when: ['place is 3', 'screen is down'], then: 'seen is at 3' },
        { name: 'see 4', when: ['place is 4'], then: 'seen is at 4' },
        { name: 'hidden at 2', when: ['place is 2', 'screen is up'], then: 'seen is nothing' },
        { name: 'hidden at 3', when: ['place is 3', 'screen is up'], then: 'seen is nothing' },
      ],
    },
    // The jobs only use what can be seen: the screen and what we see. "place" is the world's own business.
    jobs: [
      { name: 'no screen, ends at 4', start: { screen: 'down', seen: 'at 1' }, expect: 'seen is at 4' },
      { name: 'no screen, seen at 3 on step 3', start: { screen: 'down', seen: 'at 1' }, expect: 'seen is at 3', at: 3 },
      { name: 'screen up, ends at 4', start: { screen: 'up', seen: 'at 1' }, expect: 'seen is at 4' },
      { name: 'screen up, nothing on step 2', start: { screen: 'up', seen: 'at 1' }, expect: 'seen is nothing', at: 2 },
      { name: 'screen up, nothing on step 3', start: { screen: 'up', seen: 'at 1' }, expect: 'seen is nothing', at: 3 },
      { name: 'screen up, back at 4 on step 4', start: { screen: 'up', seen: 'at 1' }, expect: 'seen is at 4', at: 4, held_back: true },
      { name: 'no screen, never nothing', start: { screen: 'down', seen: 'at 1' }, expect: 'seen is nothing', at: 'never', held_back: true },
      // Added after the first runs (log entry 13): the earlier held-back jobs could not catch a rule that jumps straight to "at 4".
      { name: 'no screen, seen at 2 at some point', start: { screen: 'down', seen: 'at 1' }, expect: 'seen is at 2', at: 'ever', held_back: true, added_later: true },
    ],
  },
  {
    id: 'door-game',
    kind: 'planning a video game',
    request: 'A small game: the player can pick up a key, open a door with it, and walk through to win. Touching the ghost costs a life. With no lives left the game is over. Opening the door without the key does nothing.',
    world: {
      things: { key: ['on floor', 'carried'], door: ['locked', 'open'], lives: ['2', '1', '0'], game: ['playing', 'won', 'over'] },
      events: ['pick up key', 'use door', 'walk through', 'touch ghost'],
      start: { key: 'on floor', door: 'locked', lives: '2', game: 'playing' },
      rules: [
        { name: 'take key', when: ['pick up key happens', 'game is playing'], then: 'key is carried' },
        { name: 'unlock', when: ['use door happens', 'key is carried', 'game is playing'], then: 'door is open' },
        { name: 'win', when: ['walk through happens', 'door is open', 'game is playing'], then: 'game is won' },
        { name: 'lose a life', when: ['touch ghost happens', 'lives is 2', 'game is playing'], then: 'lives is 1' },
        { name: 'lose the last life', when: ['touch ghost happens', 'lives is 1', 'game is playing'], then: 'lives is 0' },
        { name: 'game over', when: ['lives is 0'], then: 'game is over' },
      ],
    },
    jobs: [
      { name: 'key, door, walk: win', events: ['pick up key', 'use door', 'walk through'], expect: 'game is won' },
      { name: 'door without key stays locked', events: ['use door', 'walk through'], expect: ['door is locked', 'game is playing'] },
      { name: 'one ghost touch', events: ['touch ghost'], expect: ['lives is 1', 'game is playing'] },
      { name: 'two ghost touches', events: ['touch ghost', 'touch ghost'], expect: 'game is over' },
      { name: 'walk through a locked door', events: ['pick up key', 'walk through'], expect: 'game is playing', held_back: true },
      { name: 'win then ghost', events: ['pick up key', 'use door', 'walk through', 'touch ghost'], expect: 'game is won', held_back: true },
      { name: 'over, then key', events: ['touch ghost', 'touch ghost', 'pick up key'], expect: 'key is on floor', held_back: true },
    ],
  },
  {
    id: 'lighthouse-story',
    kind: 'a story whose ending must follow',
    request: 'A story: Mara keeps a lighthouse with her brother Tev. Tev hides a letter offering Mara a job in the city. A storm comes; Tev fails to light the lamp and a boat is nearly lost; Mara lights it. Mara finds the letter. Ending: Mara stays, because she has seen Tev cannot keep the light alone. If she had not seen the storm night, finding the letter would have made her leave.',
    world: {
      things: { letter: ['hidden', 'found'], mara_knows_tev_cannot_cope: ['no', 'yes'], lamp: ['dark', 'lit'], mara: ['at lighthouse', 'gone to city', 'staying for good'] },
      events: ['storm', 'mara lights lamp', 'mara finds letter'],
      start: { letter: 'hidden', mara_knows_tev_cannot_cope: 'no', lamp: 'dark', mara: 'at lighthouse' },
      rules: [
        { name: 'storm shows Tev failing', when: ['storm happens', 'lamp is dark'], then: 'mara_knows_tev_cannot_cope is yes' },
        { name: 'Mara lights it', when: ['mara lights lamp happens'], then: 'lamp is lit' },
        { name: 'letter found', when: ['mara finds letter happens'], then: 'letter is found' },
        { name: 'leaves', when: ['letter is found', 'mara_knows_tev_cannot_cope is no', 'mara is at lighthouse'], then: 'mara is gone to city' },
        { name: 'stays', when: ['letter is found', 'mara_knows_tev_cannot_cope is yes', 'mara is at lighthouse'], then: 'mara is staying for good' },
      ],
    },
    jobs: [
      { name: 'the story as told', events: ['storm', 'mara lights lamp', 'mara finds letter'], expect: 'mara is staying for good' },
      { name: 'no storm night', events: ['mara finds letter'], expect: 'mara is gone to city' },
      { name: 'letter never found', events: ['storm', 'mara lights lamp'], expect: 'mara is at lighthouse' },
      { name: 'letter found before the storm', events: ['mara finds letter', 'storm', 'mara lights lamp'], expect: 'mara is gone to city', held_back: true },
      { name: 'storm with the lamp already lit', start: { lamp: 'lit' }, events: ['storm', 'mara finds letter'], expect: 'mara is gone to city', held_back: true },
    ],
  },
  {
    id: 'reminder-app',
    kind: 'a vague request from a user',
    request: 'I want a to-do app where things I keep putting off get more urgent, and done things go away.',
    world: {
      things: { task: ['new', 'urgent', 'overdue', 'done'], snoozes: ['0', '1', '2'] },
      events: ['snooze', 'finish', 'day passes'],
      start: { task: 'new', snoozes: '0' },
      rules: [
        { name: 'first snooze', when: ['snooze happens', 'snoozes is 0', 'task is not done'], then: 'snoozes is 1' },
        { name: 'second snooze', when: ['snooze happens', 'snoozes is 1', 'task is not done'], then: 'snoozes is 2' },
        { name: 'urgent after two snoozes', when: ['snoozes is 2', 'task is new'], then: 'task is urgent' },
        { name: 'overdue after a day when urgent', when: ['day passes happens', 'task is urgent'], then: 'task is overdue' },
        { name: 'finishing', when: ['finish happens'], then: 'task is done' },
      ],
    },
    jobs: [
      { name: 'finish a new task', events: ['finish'], expect: 'task is done' },
      { name: 'put off twice', events: ['snooze', 'snooze'], expect: 'task is urgent' },
      { name: 'nothing happens', events: [], expect: 'task is new' },
      { name: 'put off once', events: ['snooze'], expect: 'task is new', held_back: true },
      { name: 'put off twice then a day', events: ['snooze', 'snooze', 'day passes'], expect: 'task is overdue', held_back: true },
      { name: 'a day passes on a new task', events: ['day passes'], expect: 'task is new', held_back: true },
      { name: 'finish an overdue task', events: ['snooze', 'snooze', 'day passes', 'finish'], expect: 'task is done', held_back: true },
    ],
  },
];
