// Ashwake Phase 3 — Founder blind review board data.
// Alias-only. No concept identities, no specialist labels, no metric bias up front.
// Media paths are relative to this folder so the board works from file://.
window.BOARD_DATA = {
  options: [
    {
      alias: "OPTION A",
      slug: "OPTION_A",
      thesis: "A sacred care-space where failing coals are kept alive by ritual support systems and restored through readable pulse windows.",
      walkthrough: "OPTION_A/walkthrough-silent-sample.mp4",
      states: [
        { key: "spawn", label: "Spawn" },
        { key: "first_landmark", label: "First Landmark" },
        { key: "approach", label: "Approach" },
        { key: "reading", label: "Reading" },
        { key: "safe_window", label: "Safe Window" },
        { key: "hostile", label: "Hostile" },
        { key: "rejected_interaction", label: "Rejected Interaction" },
        { key: "accepted_interaction", label: "Accepted Interaction" },
        { key: "one_coal_restored", label: "One Coal Restored" },
        { key: "final_climax_direction", label: "Final / Climax Direction" },
        { key: "environment_overview", label: "Environment Overview" }
      ],
      grayscale: [
        { key: "spawn", label: "Spawn", file: "grayscale/spawn-ashwake-gameplay-00.png" },
        { key: "safe_window", label: "Safe", file: "grayscale/safe_window-ashwake-gameplay-00.png" },
        { key: "hostile", label: "Hostile", file: "grayscale/hostile-ashwake-gameplay-00.png" },
        { key: "one_coal_restored", label: "Restored", file: "grayscale/one_coal_restored-ashwake-gameplay-00.png" }
      ],
      materialSheet: "OPTION_A/material-audio/material-contact-sheet.png",
      materialsByLight: [
        { light: "Neutral light", files: [
          "OPTION_A/material-audio/materials/neutral_light/material_01.png",
          "OPTION_A/material-audio/materials/neutral_light/material_02.png",
          "OPTION_A/material-audio/materials/neutral_light/material_03.png",
          "OPTION_A/material-audio/materials/neutral_light/material_04.png",
          "OPTION_A/material-audio/materials/neutral_light/material_05.png"
        ]},
        { light: "Grazing light", files: [
          "OPTION_A/material-audio/materials/grazing_light/material_01.png",
          "OPTION_A/material-audio/materials/grazing_light/material_02.png",
          "OPTION_A/material-audio/materials/grazing_light/material_03.png",
          "OPTION_A/material-audio/materials/grazing_light/material_04.png",
          "OPTION_A/material-audio/materials/grazing_light/material_05.png"
        ]},
        { light: "Production light", files: [
          "OPTION_A/material-audio/materials/production_light/material_01.png",
          "OPTION_A/material-audio/materials/production_light/material_02.png",
          "OPTION_A/material-audio/materials/production_light/material_03.png",
          "OPTION_A/material-audio/materials/production_light/material_04.png",
          "OPTION_A/material-audio/materials/production_light/material_05.png"
        ]}
      ],
      audio: [
        { key: "ambience", label: "Ambience", file: "OPTION_A/material-audio/audio/ambience.wav" },
        { key: "reading_pulse", label: "Reading", file: "OPTION_A/material-audio/audio/reading_pulse.wav" },
        { key: "safe_signal", label: "Safe signal", file: "OPTION_A/material-audio/audio/safe_signal.wav" },
        { key: "hostile_signal", label: "Hostile signal", file: "OPTION_A/material-audio/audio/hostile_signal.wav" },
        { key: "success_response", label: "Success response", file: "OPTION_A/material-audio/audio/success_response.wav" }
      ]
    },
    {
      alias: "OPTION B",
      slug: "OPTION_B",
      thesis: "A dead fire-landscape where coals behave like buried sun-seeds and restoring one briefly changes the world around it.",
      walkthrough: "OPTION_B/walkthrough-silent-sample.mp4",
      states: [
        { key: "spawn", label: "Spawn" },
        { key: "first_landmark", label: "First Landmark" },
        { key: "approach", label: "Approach" },
        { key: "reading", label: "Reading" },
        { key: "safe_window", label: "Safe Window" },
        { key: "hostile", label: "Hostile" },
        { key: "rejected_interaction", label: "Rejected Interaction" },
        { key: "accepted_interaction", label: "Accepted Interaction" },
        { key: "one_coal_restored", label: "One Coal Restored" },
        { key: "final_climax_direction", label: "Final / Climax Direction" },
        { key: "environment_overview", label: "Environment Overview" }
      ],
      grayscale: [
        { key: "spawn", label: "Spawn", file: "grayscale/spawn-ashwake-gameplay-00.png" },
        { key: "safe_window", label: "Safe", file: "grayscale/safe_window-ashwake-gameplay-00.png" },
        { key: "hostile", label: "Hostile", file: "grayscale/hostile-ashwake-gameplay-00.png" },
        { key: "one_coal_restored", label: "Restored", file: "grayscale/one_coal_restored-ashwake-gameplay-00.png" }
      ],
      materialSheet: "OPTION_B/material-audio/material-contact-sheet.png",
      materialsByLight: [
        { light: "Neutral light", files: [
          "OPTION_B/material-audio/materials/neutral_light/material_01.png",
          "OPTION_B/material-audio/materials/neutral_light/material_02.png",
          "OPTION_B/material-audio/materials/neutral_light/material_03.png",
          "OPTION_B/material-audio/materials/neutral_light/material_04.png",
          "OPTION_B/material-audio/materials/neutral_light/material_05.png"
        ]},
        { light: "Grazing light", files: [
          "OPTION_B/material-audio/materials/grazing_light/material_01.png",
          "OPTION_B/material-audio/materials/grazing_light/material_02.png",
          "OPTION_B/material-audio/materials/grazing_light/material_03.png",
          "OPTION_B/material-audio/materials/grazing_light/material_04.png",
          "OPTION_B/material-audio/materials/grazing_light/material_05.png"
        ]},
        { light: "Production light", files: [
          "OPTION_B/material-audio/materials/production_light/material_01.png",
          "OPTION_B/material-audio/materials/production_light/material_02.png",
          "OPTION_B/material-audio/materials/production_light/material_03.png",
          "OPTION_B/material-audio/materials/production_light/material_04.png",
          "OPTION_B/material-audio/materials/production_light/material_05.png"
        ]}
      ],
      audio: [
        { key: "ambience", label: "Ambience", file: "OPTION_B/material-audio/audio/ambience.wav" },
        { key: "reading_pulse", label: "Reading", file: "OPTION_B/material-audio/audio/reading_pulse.wav" },
        { key: "safe_signal", label: "Safe signal", file: "OPTION_B/material-audio/audio/safe_signal.wav" },
        { key: "hostile_signal", label: "Hostile signal", file: "OPTION_B/material-audio/audio/hostile_signal.wav" },
        { key: "success_response", label: "Success response", file: "OPTION_B/material-audio/audio/success_response.wav" }
      ]
    },
    {
      alias: "OPTION C",
      slug: "OPTION_C",
      thesis: "A heat-infrastructure sanctuary where ancient coals must be rekindled by reading physical timing cues in the world itself.",
      walkthrough: "OPTION_C/walkthrough-silent-sample.mp4",
      states: [
        { key: "spawn", label: "Spawn" },
        { key: "first_landmark", label: "First Landmark" },
        { key: "approach", label: "Approach" },
        { key: "reading", label: "Reading" },
        { key: "safe_window", label: "Safe Window" },
        { key: "hostile", label: "Hostile" },
        { key: "rejected_interaction", label: "Rejected Interaction" },
        { key: "accepted_interaction", label: "Accepted Interaction" },
        { key: "one_coal_restored", label: "One Coal Restored" },
        { key: "final_climax_direction", label: "Final / Climax Direction" },
        { key: "environment_overview", label: "Environment Overview" }
      ],
      grayscale: [
        { key: "spawn", label: "Spawn", file: "grayscale/spawn-ashwake-gameplay-00.png" },
        { key: "safe_window", label: "Safe", file: "grayscale/safe_window-ashwake-gameplay-00.png" },
        { key: "hostile", label: "Hostile", file: "grayscale/hostile-ashwake-gameplay-00.png" },
        { key: "one_coal_restored", label: "Restored", file: "grayscale/one_coal_restored-ashwake-gameplay-00.png" }
      ],
      materialSheet: "OPTION_C/material-audio/material-contact-sheet.png",
      materialsByLight: [
        { light: "Neutral light", files: [
          "OPTION_C/material-audio/materials/neutral_light/material_01.png",
          "OPTION_C/material-audio/materials/neutral_light/material_02.png",
          "OPTION_C/material-audio/materials/neutral_light/material_03.png",
          "OPTION_C/material-audio/materials/neutral_light/material_04.png",
          "OPTION_C/material-audio/materials/neutral_light/material_05.png"
        ]},
        { light: "Grazing light", files: [
          "OPTION_C/material-audio/materials/grazing_light/material_01.png",
          "OPTION_C/material-audio/materials/grazing_light/material_02.png",
          "OPTION_C/material-audio/materials/grazing_light/material_03.png",
          "OPTION_C/material-audio/materials/grazing_light/material_04.png",
          "OPTION_C/material-audio/materials/grazing_light/material_05.png"
        ]},
        { light: "Production light", files: [
          "OPTION_C/material-audio/materials/production_light/material_01.png",
          "OPTION_C/material-audio/materials/production_light/material_02.png",
          "OPTION_C/material-audio/materials/production_light/material_03.png",
          "OPTION_C/material-audio/materials/production_light/material_04.png",
          "OPTION_C/material-audio/materials/production_light/material_05.png"
        ]}
      ],
      audio: [
        { key: "ambience", label: "Ambience", file: "OPTION_C/material-audio/audio/ambience.wav" },
        { key: "reading_pulse", label: "Reading", file: "OPTION_C/material-audio/audio/reading_pulse.wav" },
        { key: "safe_signal", label: "Safe signal", file: "OPTION_C/material-audio/audio/safe_signal.wav" },
        { key: "hostile_signal", label: "Hostile signal", file: "OPTION_C/material-audio/audio/hostile_signal.wav" },
        { key: "success_response", label: "Success response", file: "OPTION_C/material-audio/audio/success_response.wav" }
      ]
    }
  ],

  // Section 6 — recorded BEFORE any instructional text, per option.
  noHudComprehension: [
    "What do you think the objective is?",
    "Where do you think you should go?",
    "What do you think is interactable?",
    "What do you think SAFE means?",
    "What do you think HOSTILE means?",
    "What do you think restoration accomplished?"
  ],

  // Section 7 — state recognition. Intended state hidden until answer recorded.
  stateTest: {
    presentation: [
      { slot: 1, key: "safe" },
      { slot: 2, key: "dangerous" },
      { slot: 3, key: "success" },
      { slot: 4, key: "failure" }
    ],
    question: "What do you think is happening?",
    feelings: ["safe", "dangerous", "opportunity", "success", "failure", "unclear"],
    confidence: ["LOW", "MEDIUM", "HIGH"]
  },

  // Section 8 — twenty questions per option.
  founderQuestions: [
    "What do you think this place is?",
    "What happened here?",
    "What do you think your objective is?",
    "Where did your eye go first?",
    "Did you know where to move?",
    "What did you think was interactable?",
    "Could you recognize the safe opportunity?",
    "Could you recognize danger?",
    "Did restoring a coal visibly matter?",
    "What felt most convincing?",
    "What looked primitive?",
    "What confused you?",
    "What felt generic?",
    "What felt original?",
    "What visual element do you remember most?",
    "What sound do you remember most?",
    "Did the environment feel like a real place or a test level?",
    "Would you want to explore more of this world?",
    "What would prevent this from feeling like a professional released game?",
    "What would you preserve at all costs?"
  ],

  // Section 9 — cross-option, shown only after all three options are submitted.
  crossOptionQuestions: [
    "Which world makes you most curious?",
    "Which world has the strongest identity?",
    "Which is easiest to understand without HUD?",
    "Which has the clearest SAFE/HOSTILE language?",
    "Which restoration feels most meaningful?",
    "Which feels most like an actual place?",
    "Which feels closest to professional game quality?",
    "Which has the strongest long-term world potential?",
    "Which would you personally want to continue playing?",
    "Which one should Ashwake become?"
  ],

  crossOptionFacets: [
    "BEST OVERALL",
    "BEST GAMEPLAY",
    "BEST WORLD",
    "BEST ART DIRECTION",
    "BEST EMOTIONAL IDENTITY"
  ]
};
