import { ProjectAudience } from "../components/project/ProjectAudience";
import "../components/project/project-motion.css";

import { DeveloperProfile } from "../components/project/DeveloperProfile";
import { EngineeringJourney } from "../components/project/EngineeringJourney";
import { EngineeringPrinciples } from "../components/project/EngineeringPrinciples";
import { ProjectHero } from "../components/project/ProjectHero";
import { ProjectOverview } from "../components/project/ProjectOverview";
import { ProjectReflection } from "../components/project/ProjectReflection";
import { TechnologyStack } from "../components/project/TechnologyStack";

export function ProjectPage() {
  return (
    <div
      className={[
        "project-page",
        "space-y-[var(--space-7)]",
      ].join(" ")}
    >
      <ProjectHero />

      <ProjectOverview />



      <ProjectAudience />

      <EngineeringJourney />

      <EngineeringPrinciples />

      <TechnologyStack />

      <DeveloperProfile />

      <ProjectReflection />
    </div>
  );
}
