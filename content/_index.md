---
# Leave the homepage title empty to use the site title
title: ''
summary: ''
date: 2026-06-15
type: landing

sections:
  # ──────────────────────────────────────────────────────────────────────
  # BIO
  # ──────────────────────────────────────────────────────────────────────
  - block: resume-biography-3
    content:
      username: me
      text: ''
      button:
        text: ''
        url: ''
      headings:
        about: ''
        education: ''
        interests: 'Research interests'
    design:
      background:
        gradient_mesh:
          enable: false
      name:
        size: md
      avatar:
        size: medium
        shape: circle

  # ──────────────────────────────────────────────────────────────────────
  # RESEARCH (narrative sections, one per research line)
  # ──────────────────────────────────────────────────────────────────────
  - block: markdown
    id: research
    content:
      title: 'Research'
      subtitle: ''
      text: |-
        ![Research wordcloud](media/wordcloud.png)

        ### Exercise physiology & human performance

        My work examines the physiological factors that shape human performance across sprint and endurance contexts. I am particularly interested in how metabolic, cardiopulmonary, muscular, and contextual factors interact to determine what athletes can produce, sustain, and repeat.

        ### Performance modelling & concepts of limitation

        I study how performance emerges from the interaction of physiology, environment, pacing, equipment, competition, and sport-specific demands. This includes a conceptual focus on how constructs such as durability, fatigability, fatigue resistance, repeatability, and resilience are defined and applied across sports. Rather than assuming one universal model of performance, I am interested in models that respect the specific demands of different sports, disciplines, and competitive contexts.

        ### Exercise bioenergetics, lactate & glycolytic metabolism

        A central part of my research focuses on the bioenergetics of exercise, especially lactate dynamics and glycolytic metabolism. I study how sprint-derived indices such as vLamax and vLapeak can be defined, measured, and interpreted, and how they relate to metabolic thresholds, aerobic capacity, and performance.

        ### Sex differences, body composition & scaling

        I am interested in how sex differences, body composition, and scaling approaches shape the interpretation of physiological and performance data. This includes questions about when variables should be expressed relative to body mass, fat-free mass, or alternative scaling models, and how these decisions influence comparisons between athletes, groups, and sexes.
    design:
      columns: '1'

  # ──────────────────────────────────────────────────────────────────────
  # PUBLICATIONS
  # ──────────────────────────────────────────────────────────────────────
  - block: content-collection
    id: publications
    content:
      title: Featured Publications
      filters:
        folders:
          - publications
        featured_only: true
    design:
      view: citation
      columns: 2

  - block: content-collection
    content:
      title: Recent Publications
      text: ''
      count: 0
      filters:
        folders:
          - publications
        exclude_featured: false
    design:
      view: citation-plain

  # ──────────────────────────────────────────────────────────────────────
  # TEACHING
  # ──────────────────────────────────────────────────────────────────────
  - block: markdown
    id: teaching
    content:
      title: 'Teaching'
      subtitle: ''
      text: |-
        I teach in sport and movement science at FAU Erlangen-Nürnberg, with a
        focus on Lehramt Sport (PE teacher training). There, I focus on Basketball and
        try to share my love for the game. I also teach other subjects, most notably small games and
        how they’re used for understanding rules.

        My research associate position includes a
        university statistics course built around a flipped-classroom model,
        and an ongoing interest in how AI tools — used thoughtfully — can
        support both PE teaching and the way students learn to work with data.
    design:
      columns: '1'

  # ──────────────────────────────────────────────────────────────────────
  # TALKS & OUTREACH
  # ──────────────────────────────────────────────────────────────────────
  - block: content-collection
    id: talks
    content:
      title: Talks & Outreach
      filters:
        folders:
          - events
    design:
      view: card

  - block: content-collection
    id: outreach
    content:
      title: Outreach
      count: 0
      filters:
        folders:
          - outreach
    design:
      view: outreach-card

  # ──────────────────────────────────────────────────────────────────────
  # CONTACT
  # ──────────────────────────────────────────────────────────────────────
  - block: markdown
    id: contact
    content:
      title: '✉️ Contact'
      subtitle: ''
      text: |-
        The best way to reach me is by email — see the links at the top of
        this page for email and social/academic profiles (ORCID,
        ResearchGate, Bluesky).

        I'm always happy to hear from potential collaborators, students, or
        journalists working on topics related to exercise physiology,
        performance diagnostics, or ball games and physical education.
    design:
      columns: '1'
---
