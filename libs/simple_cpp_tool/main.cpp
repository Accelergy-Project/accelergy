#include "accelergyComponent.h"
#include "mac.h"
#include "PE.h"
#include "accelergy.h"


int main() {
  /* construct a design with a mac, and two scratchpads */
  string design_name = "my_design";
  Accelergy accelergyDesign = Accelergy(design_name);

  memory *glb = new memory("glb", true, map<string, string>{{"width", "16"}, {"depth", "2"}, {"nbanks", "2"}});
  accelergyDesign.add_top_level_component(glb);

  PE *my_PE = new PE("my_PE", 16, 2,20);
  accelergyDesign.add_top_level_component(my_PE);

  // collect architecture description
  accelergyDesign.register_design_architecture();

  /* psudo simulation */
  my_PE->process_job(3,7,5);
  my_PE->process_job(5,0,5);

  // collect action counts
  accelergyDesign.register_design_action_counts();

  return 0;
}
