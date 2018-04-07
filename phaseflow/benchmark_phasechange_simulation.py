""" **benchmark_phasechange_simulation.py** applies the phase-change model to a variety of benchmark problems. """
import fenics
import phaseflow


class BenchmarkPhaseChangeSimulation(phaseflow.phasechange_simulation.PhaseChangeSimulation):
    """ This extends `phaseflow.octadecane.Simulation` with verification methods. """
    def __init__(self):
        """ This extends the `__init__` method to append the output directory. """
        phaseflow.phasechange_simulation.PhaseChangeSimulation.__init__(self)
        
        self.output_dir += "benchmark/"

    
    def run(self, verify = True):
        """ Extend the `phaseflow.octadecane.Simulation.run` method to add a final verification step. 
        
        Parameters
        ----------
        verify : bool
        
            This will only call the `self.verify` method if True.
        """
        phaseflow.phasechange_simulation.PhaseChangeSimulation.run(self)
        
        if verify:
        
            self.verify()
        
        
    def verify(self):
        """ Verify the result.
        
        This base method is written so fail, so this must be overloaded with an benchmark specific method.
        """
        assert(False)
        
    
    def verify_scalar_solution_component(self, 
            component, 
            coordinates, 
            verified_values, 
            relative_tolerance, 
            absolute_tolerance):
        """ Verify the scalar values of a specified solution component.
        
        Parameters
        ----------
        component : integer
        
            The solution is often vector-valued and based on a mixed formulation.
            By having the user specify a component to verify with this function,
            we can write the rest of the function quite generally.
            
        coordinates : list of tuples, where each tuple contains a float for each spatial dimension.
        
            Each tuple will be converted to a `Point`.
            
        verified_values : tuple of floats
        
           Point-wise verified values from a benchmark publication.
           
        relative_tolerance : float   
           
           This will be used for asserting that the relative error is not too large.
           
        absolute_tolerance : float
        
            For small values, the absolute error will be checked against this tolerance,
            instead of considering the relative error.
        """
        assert(len(verified_values) == len(coordinates))
        
        for i, verified_value in enumerate(verified_values):
        
            point = phaseflow.helpers.Point(coordinates[i])
            
            if self.mesh.bounding_box_tree().collides_entity(point):
            
                values = self.state.solution.leaf_node()(point)
                
                value = values[component]
                
                absolute_error = abs(value - verified_value)
                
                if abs(verified_value) > absolute_tolerance:
                
                    relative_error = absolute_error/verified_value
               
                    assert(relative_error < relative_tolerance)
                    
                else:
                
                    assert(absolute_error < absolute_tolerance)
        
    
class CavityBenchmarkPhaseChangeSimulation(BenchmarkPhaseChangeSimulation):
    """ This extends the BenchmarkSimulation class with attributes and methods specific to 
        rectangular cavity benchmarks.
    
    This extension focuses on sizing the cavity and making the corresponding mesh.
    """
    def __init__(self):
        """ Extend the `init` method with attributes needed for sizing the cavity. """
        BenchmarkPhaseChangeSimulation.__init__(self)
        
        self.mesh_size = (2, 2)

        self.xmin = 0.
        
        self.ymin = 0.
        
        self.zmin = None
        
        self.xmax = 1.
        
        self.ymax = 1.
        
        self.zmax = None
        
        
    def validate_attributes(self):
        """ Validate attributes to improve user friendliness. 
        
        When working with a unit square domain and uniform initial refinement, 
        often it is more intuitive to only specify a single integer for the grid sizing.
        """
        if type(self.mesh_size) is type(20):
        
            self.mesh_size = (self.mesh_size, self.mesh_size)
        
        
    def setup_derived_attributes(self):
        """ Set attributes which should not be touched by the user. 
        
        These are mostly strings which are used as arguments to `fenics.DirichletBC`
        for specifying where the boundary conditions should be applied.
        """
        BenchmarkPhaseChangeSimulation.setup_derived_attributes(self)
        
        self.left_wall = "near(x[0],  xmin)".replace("xmin", str(self.xmin))
        
        self.right_wall = "near(x[0],  xmax)".replace("xmax", str(self.xmax))
        
        self.bottom_wall = "near(x[1],  ymin)".replace("ymin",  str(self.ymin))
        
        self.top_wall = "near(x[1],  ymax)".replace("ymax", str(self.ymax))
        
        self.walls = \
                self.top_wall + " | " + self.bottom_wall + " | " + self.left_wall + " | " + self.right_wall
        
        if len(self.mesh_size) == 3:
        
            self.back_wall = "near(x[2],  zmin)".replace("zmin",  str(self.zmin))
        
            self.front_wall = "near(x[2],  zmax)".replace("zmax", str(self.zmax))
        
            self.walls += " | " + self.back_wall + " | " + self.front_wall
        
        
    def setup_coarse_mesh(self):
        """ This creates the rectangular mesh, or rectangular prism in 3D. """
        if len(self.mesh_size) == 2:
        
            self.mesh = fenics.RectangleMesh(fenics.mpi_comm_world(), 
                fenics.Point(self.xmin, self.ymin), fenics.Point(self.xmax, self.ymax),
                self.mesh_size[0], self.mesh_size[1], "crossed")

        elif len(self.mesh_size) == 3:
        
            self.mesh = fenics.BoxMesh(fenics.mpi_comm_world(), 
                fenics.Point(self.xmin, self.ymin, self.zmin),
                fenics.Point(self.xmax, self.ymax, self.zmax),
                self.mesh_size[0], self.mesh_size[1], self.mesh_size[2])
  
  
class LidDrivenCavityBenchmarkPhaseChangeSimulation(CavityBenchmarkPhaseChangeSimulation):
    """ This class implements the lid-driven cavity benchmark. """
    def __init__(self):
        """ Extend the `init` method with attributes for the lid-driven cavity benchmark.

        The tolerances set here are used for verification testing.
        """
        CavityBenchmarkPhaseChangeSimulation.__init__(self)
        
        self.relative_tolerance = 3.e-2
        
        self.absolute_tolerance = 1.e-2
        
        self.timestep_size = 1.e12
        
        self.liquid_viscosity = 0.01
        
        self.end_time = 0. + self.timestep_size
        
        self.output_dir += "lid_driven_cavity/"
        
        self.adaptive_goal_tolerance = 1.e-4
  
    
    def setup_derived_attributes(self):
        """ Add attributes for the boundary conditions which should not be modified directly. """
        CavityBenchmarkPhaseChangeSimulation.setup_derived_attributes(self)
        
        self.fixed_walls = self.bottom_wall + " | " + self.left_wall + " | " + self.right_wall
        
        self.boundary_conditions = [
            {"subspace": 1, "location": self.top_wall, "value": (1., 0.)},
            {"subspace": 1, 
             "location": self.fixed_walls, 
             "value": (0., 0.)}]
  
  
    def setup_initial_values(self):
        """ Set initial values which are consistent with the boundary conditions. """
        self.old_state.interpolate(("0.", self.top_wall, "0.", "1."))
    
    
    def setup_adaptive_goal_form(self):
        """ Set an adaptive goal based on the horizontal velocity. """
        p, u, T = fenics.split(self.state.solution)
        
        self.adaptive_goal_form = u[0]*u[0]*self.integration_metric
        
    
    def verify(self):
        """ Verify against @cite{ghia1982}. """
        self.verify_scalar_solution_component(
            component = 1,
            coordinates = [(0.5, y) 
                for y in [1.0000, 0.9766, 0.1016, 0.0547, 0.0000]],
            verified_values = [1.0000, 0.8412, -0.0643, -0.0372, 0.0000],
            relative_tolerance = self.relative_tolerance,
            absolute_tolerance = self.absolute_tolerance)
 
        
class LDCBenchmarkPhaseChangeSimulationWithSolidSubdomain(LidDrivenCavityBenchmarkPhaseChangeSimulation):
    """ This class extends the lid-driven cavity with a solid subdomain to test variable viscosity.
    
    The unit square from the original benchmark is prescribed a temperature which makes it fluid,
    while below the original bottom wall, a cold temperature is prescribed, making it solid.
    """
    def __init__(self):
    
        LidDrivenCavityBenchmarkPhaseChangeSimulation.__init__(self)
        
        self.ymin = -0.25
        
        self.y_pci = 0.
        
        self.mesh_size = (4, 5)
        
        self.pci_refinement_cycles = 4
        
        self.timestep_size = 20.
        
        self.relative_tolerance = 8.e-2  # @todo This is quite large.
        
        self.absolute_tolerance = 2.e-2
        
        self.adaptive_goal_tolerance = 1.e-5
                
        self.prandtl_number = 1.e16
        
        self.liquid_viscosity = 0.01
        
        self.solid_viscosity = 1.e6
        
        self.stefan_number = 1.e16
        
        self.regularization_central_temperature = -0.01
        
        self.regularization_smoothing_parameter = 0.01
        
        self.end_time = 2.*self.timestep_size
        
        self.quadrature_degree = 3
        
        self.output_dir += "with_solid_subdomain/"
        
    
    def setup_derived_attributes(self):
        """ Add attributes for the boundary conditions which should not be modified directly. """
        LidDrivenCavityBenchmarkPhaseChangeSimulation.setup_derived_attributes(self)
    
        self.boundary_conditions = [
                {"subspace": 1, "location": self.top_wall, "value": (1., 0.)},
                {"subspace": 1, "location": self.fixed_walls, "value": (0., 0.)}]
    
    
    def setup_coarse_mesh(self):
        """ Use the coarse mesh from the lid-driven cavity benchmark. """
        LidDrivenCavityBenchmarkPhaseChangeSimulation.setup_coarse_mesh(self)

        
    def refine_initial_mesh(self):
        """ Refine near the phase-change interface. """
        y_pci = self.y_pci
        
        class PhaseInterface(fenics.SubDomain):
            
            def inside(self, x, on_boundary):
            
                return fenics.near(x[1], y_pci)
        
        
        phase_interface = PhaseInterface()
        
        for i in range(self.pci_refinement_cycles):
            
            edge_markers = fenics.MeshFunction("bool", self.mesh, 1, False)
            
            phase_interface.mark(edge_markers, True)

            fenics.adapt(self.mesh, edge_markers)
            
            self.mesh = self.mesh.child()  # Does this break references? Can we do this a different way?
            
    
    def setup_initial_values(self):
        """ Set initial values such that the temperature corresponds to 
            liquid or solid phases on either side of the phase-change interface.
        """
        temperature_string = "1. - 2.*(x[1] <= y_pci)".replace("y_pci", str(self.y_pci))
                
        self.old_state.interpolate(("0.",  self.top_wall, "0.", temperature_string))


class HeatDrivenCavityBenchmarkPhaseChangeSimulation(CavityBenchmarkPhaseChangeSimulation):
    """ This class implements the heat-driven cavity benchmark. """
    def __init__(self):
        """ Extend the `__init__` method for the heat-driven cavity benchmark. 
        
        The tolerances set here are used during verification testing.
        """
        CavityBenchmarkPhaseChangeSimulation.__init__(self)
        
        self.end_time = None
        
        self.hot_wall_temperature = 0.5
    
        self.cold_wall_temperature = -self.hot_wall_temperature
        
        self.solid_viscosity = 1.
        
        self.stefan_number = 1.e32
        
        self.rayleigh_number = 1.e6
        
        self.prandtl_number = 0.71
        
        self.timestep_size = 1.e-3
        
        self.stop_when_steady = True
        
        self.steady_relative_tolerance = 1.e-4
        
        self.output_dir += "heat_driven_cavity/"
        
        self.adaptive_goal_tolerance = 20.
        
        
    def do_between_timesteps(self):
        """ Keep doubling the time step size to quickly reach steady state. """
        CavityBenchmarkPhaseChangeSimulation.do_between_timesteps(self)
        
        self.set_timestep_size(2.*self.timestep_size)
        
        
    def setup_derived_attributes(self):
        """ Add attributes which should not be modified directly,
            related to the boundary conditions and initial values.
        """
        CavityBenchmarkPhaseChangeSimulation.setup_derived_attributes(self)
        
        T_hot = fenics.Constant(self.hot_wall_temperature)
        
        T_cold = fenics.Constant(self.cold_wall_temperature)
        
        self.boundary_conditions = [
            {"subspace": 1, "location": self.walls, "value": (0., 0.)},
            {"subspace": 2, "location": self.left_wall, "value": T_hot},
            {"subspace": 2, "location": self.right_wall, "value": T_cold}]
            
        self.initial_temperature = "T_hot + x[0]*(T_cold - T_hot)"
        
        self.initial_temperature = self.initial_temperature.replace("T_hot", str(self.hot_wall_temperature))
        
        self.initial_temperature = self.initial_temperature.replace("T_cold", str(self.cold_wall_temperature))
        
        
    def setup_initial_values(self):
        """ Set the initial values. """
        self.old_state.interpolate(("0.", "0.", "0.", self.initial_temperature))
        
        
    def setup_adaptive_goal_form(self):
        """ Set the same goal as for the lid-driven cavity benchmark. """
        LidDrivenCavityBenchmarkPhaseChangeSimulation.setup_adaptive_goal_form(self)
        
        
    def verify(self):
        """ Verify against the result published in @cite{wang2010comprehensive}. """
        self.verify_scalar_solution_component(
            component = 1,
            coordinates = [((self.xmin + self.xmax)/2., y) for y in [0., 0.15, 0.35, 0.5, 0.65, 0.85, 1.]],
            verified_values = [val*self.rayleigh_number**0.5/self.prandtl_number
                for val in [0.0000, -0.0649, -0.0194, 0.0000, 0.0194, 0.0649, 0.0000]],
            relative_tolerance = 1.e-2,
            absolute_tolerance = 1.e-2*0.0649*self.rayleigh_number**0.5/self.prandtl_number)

   
class StefanProblemBenchmarkPhaseChangeSimulation(BenchmarkPhaseChangeSimulation):
    """ This class implements the 1D Stefan problem benchmark. """
    def __init__(self):
        """ Extend the `__init__` method for the Stefan problem. 
        
        The initial mesh refinement and tolerances set here are used during verification testing.
        """
        BenchmarkPhaseChangeSimulation.__init__(self)
        
        self.initial_uniform_cell_count = 4
        
        self.initial_hot_boundary_refinement_cycles = 8
        
        self.initial_pci_position = None  # When None, the position will be set by a rule.
        
        self.hot_wall_temperature = 1.
        
        self.cold_wall_temperature = -0.01
        
        self.stefan_number = 0.045
        
        self.gravity = (0.,)  # The Stefan problem does not consider momentum.
        
        self.regularization_smoothing_parameter = 0.005
        
        self.timestep_size = 1.e-3
        
        self.end_time = 0.1
        
        self.output_dir += "stefan_problem/"
        
        self.adaptive_goal_tolerance = 1.e-6
        
        self.relative_tolerance = 2.e-2
        
        self.absolute_tolerance = 1.e-2
        
        self.nonlinear_solver_relaxation = 0.45
        
        self.nonlinear_solver_max_iterations = 200
        
        
    def setup_derived_attributes(self):
        """ Add attributes which should not be modified directly,
            related to the boundary conditions and initial values.
        """
        BenchmarkPhaseChangeSimulation.setup_derived_attributes(self)
        
        T_hot = fenics.Constant(self.hot_wall_temperature)
        
        T_cold = fenics.Constant(self.cold_wall_temperature)
        
        self.boundary_conditions = [
            {"subspace": 2, "location": "near(x[0],  0.)", "value": T_hot},
            {"subspace": 2, "location": "near(x[0],  1.)", "value": T_cold}]
        
        if self.initial_pci_position is None:
            """ Set the initial PCI position such that the melted area is covered by one layer of cells. """
            initial_pci_position = 1./float(self.initial_uniform_cell_count)/2.**( \
                self.initial_hot_boundary_refinement_cycles - 1)
                
        else:
        
            initial_pci_position = self.initial_pci_position
        
        initial_temperature = "(T_hot - T_cold)*(x[0] < initial_pci_position) + T_cold"
        
        initial_temperature = initial_temperature.replace("initial_pci_position", str(initial_pci_position))
        
        initial_temperature = initial_temperature.replace("T_hot", str(self.hot_wall_temperature))
        
        self.initial_temperature = initial_temperature.replace("T_cold", str(self.cold_wall_temperature))
        
    
    def setup_coarse_mesh(self):
        """ Set the 1D mesh """
        self.mesh = fenics.UnitIntervalMesh(self.initial_uniform_cell_count)
        
        
    def refine_initial_mesh(self):
        """ Locally refine near the hot boundary """
        for i in range(self.initial_hot_boundary_refinement_cycles):
            
            cell_markers = fenics.MeshFunction("bool", self.mesh, self.mesh.topology().dim(), False)
            
            cell_markers.set_all(False)
            
            for cell in fenics.cells(self.mesh):
                
                found_left_boundary = False
                
                for vertex in fenics.vertices(cell):
                    
                    if fenics.near(vertex.x(0), 0.):
                        
                        found_left_boundary = True
                        
                        break
                        
                if found_left_boundary:
                    
                    cell_markers[cell] = True
                    
                    break # There should only be one such point in 1D.
                    
            self.mesh = fenics.refine(self.mesh, cell_markers)  # Does this break references?
    
    
    def setup_initial_values(self):
        """ Set the initial values. """
        self.old_state.interpolate(("0.", "0.", self.initial_temperature))
        
        
    def setup_adaptive_goal_form(self):
        """ Set the adaptive goal based on the semi-phase-field. 
        
        Here the integrated goal is equivalent to the remaining solid area.
        """
        p, u, T = fenics.split(self.state.solution)
        
        phi, dphi = self.make_semi_phasefield_function_and_its_derivative()
        
        self.adaptive_goal_form = phi(T)*self.integration_metric
        
        
    def setup_initial_guess(self):
        """ Set a zero initial guess for the Newton method.
        
        By default Phaseflow usually uses the latest solution (or the initial values) as the initial guess.
        For the special case of the 1D Stefan problem, that approach has failed.
        One might want to investigate this.
        """
        self.initial_guess = ("0.", "0.", "0.")
    

    def verify(self):
        """ Verify against analytical solution. """
        self.verify_scalar_solution_component(
            component = 2,
            coordinates = [0.00, 0.025, 0.050, 0.075, 0.10, 0.5, 1.],
            verified_values = [1.0, 0.73, 0.47, 0.20, 0.00, -0.01, -0.01],
            relative_tolerance = self.relative_tolerance,
            absolute_tolerance = self.absolute_tolerance)

            
class StefanProblemBenchmarkPhaseChangeSimulation_BDF2(StefanProblemBenchmarkPhaseChangeSimulation):

    def __init__(self):
    
        StefanProblemBenchmarkPhaseChangeSimulation.__init__(self)
        
        self.second_order_time_discretization = True
        
        self.timestep_size = 4.e-3
        
        self.adaptive_goal_tolerance = 1.e-7
        
        self.output_dir += "bdf2/"
        
        
    def apply_time_discretization(self, Delta_t, u):
    
        u_t = phaseflow.backward_difference_formulas.apply_bdf2(Delta_t, u)
        
        return u_t
        
        
    def setup_initial_guess(self):
        
        self.state.set_from_other_state(self.old_state)
        
        
class ConvectionCoupledMeltingOctadecanePCMBenchmarkPCSimulation(CavityBenchmarkPhaseChangeSimulation):
    """ This class implements the convection-coupled octadecane melting benchmark."""
    def __init__(self):
        """ Extend the `__init__` method for the octadecane melting benchmark. 
        
        The initial refinement and tolerances set here are used for verification testing.
        
        The test suite includes a regression test which will run this for a shorter simulated time.
        """
        CavityBenchmarkPhaseChangeSimulation.__init__(self)
        
        self.hot_wall_temperature = 1.
        
        self.cold_wall_temperature = -0.01
        
        self.stefan_number = 0.045      
        
        self.prandtl_number = 56.2
        
        self.rayleigh_number = 3.27e5
        
        self.gravity = (0., -1.)
        
        self.solid_viscosity = 1.e8
        
        self.liquid_viscosity = 1.
        
        self.regularization_central_temperature = 0.01
        
        self.regularization_smoothing_parameter = 0.025  # This is larger than in @cite{danaila2014newton}
        
        self.timestep_size = 1.
        
        self.quadrature_degree = 8  # The exact quadrature rule yields too many quadrature points.
        
        self.initial_hot_wall_refinement_cycles = 6
        
        self.initial_mesh_size = (1, 1)
        
        self.initial_pci_position = None
        
        self.adaptive_goal_tolerance = 1.e-5
        
        self.end_time = 80.  # This is close to the time of interest published in @{danaila2014newton}
        
        self.output_dir += "convection_coupled_melting/"
        
        self.coarsen_between_timesteps = True
        
        
    def setup_derived_attributes(self):
        """ Add attributes which should not be modified directly,
            related to the boundary conditions and initial values.
        """
        CavityBenchmarkPhaseChangeSimulation.setup_derived_attributes(self)
        
        T_hot = fenics.Constant(self.hot_wall_temperature)
        
        T_cold = fenics.Constant(self.cold_wall_temperature)
        
        self.boundary_conditions = [
                {"subspace": 1, "location": self.walls, "value": (0., 0.)},
                {"subspace": 2, "location": self.left_wall, "value": T_hot},
                {"subspace": 2, "location": self.right_wall, "value": T_cold}]
                
        if self.initial_pci_position == None:
            """ Set the initial PCI position such that the melted area is covered by one layer of cells. """
            initial_pci_position = \
                1./float(self.initial_mesh_size[0])/2.**(self.initial_hot_wall_refinement_cycles - 1)
        
        else:
        
            initial_pci_position = 0. + self.initial_pci_position
        
        initial_temperature = "(T_hot - T_cold)*(x[0] < initial_pci_position) + T_cold"
        
        initial_temperature = initial_temperature.replace("initial_pci_position", str(initial_pci_position))
        
        initial_temperature = initial_temperature.replace("T_hot", str(self.hot_wall_temperature))
        
        initial_temperature = initial_temperature.replace("T_cold", str(self.cold_wall_temperature))
        
        self.initial_temperature = initial_temperature
        
    
    def setup_coarse_mesh(self):
        """ Set a cavity mesh. """
        CavityBenchmarkPhaseChangeSimulation.setup_coarse_mesh(self)
        
    
    def refine_initial_mesh(self):
        """ Refine near the hot wall. """
        class HotWall(fenics.SubDomain):
    
            def inside(self, x, on_boundary):
            
                return on_boundary and fenics.near(x[0], 0.)

    
        hot_wall = HotWall()
        
        for i in range(self.initial_hot_wall_refinement_cycles):
            
            edge_markers = fenics.MeshFunction("bool", self.mesh, 1, False)
            
            hot_wall.mark(edge_markers, True)

            fenics.adapt(self.mesh, edge_markers)
        
            self.mesh = self.mesh.child()
        
    
    def setup_initial_values(self):
        """ Set the initial values. """
        self.old_state.interpolate(("0.", "0.", "0.", self.initial_temperature))
        
        
    def setup_adaptive_goal_form(self):
        """ Set the same goal as for the Stefan problem benchmark. """
        StefanProblemBenchmarkPhaseChangeSimulation.setup_adaptive_goal_form(self)
     
     
class CCMOctadecanePCMBenchmarkPCSimulation3D(ConvectionCoupledMeltingOctadecanePCMBenchmarkPCSimulation):
    """ This class extends the octadecane melting benchmark to 3D. """
    def __init__(self):
    
        ConvectionCoupledMeltingOctadecanePCMBenchmarkSimulation.__init__(self)
        
        self.mesh_size = (1, 1, 1)
        
        self.gravity = (0., -1., 0.)
        
        self.depth_3d = 0.5
        
        
    def setup_derived_attributes(self):
        """ Extend the boundary condition definitions to 3D. """
        ConvectionCoupledMeltingOctadecanePCMBenchmarkSimulation.setup_derived_attributes(self)
        
        self.zmin = -self.depth_3d/2.
        
        self.zmax = self.depth_3d/2.

        T_hot = fenics.Constant(self.hot_wall_temperature)
        
        T_cold = fenics.Constant(self.cold_wall_temperature)
        
        self.boundary_conditions = [
                {"subspace": 1, "location": self.walls, "value": (0., 0., 0.)},
                {"subspace": 2, "location": self.left_wall, "value": T_hot},
                {"subspace": 2, "location": self.right_wall, "value": T_cold}]
                
        
    def refine_initial_mesh(self):
        """ Replace 2D refinement method with 3D method. Perhaps one could make an n-dimensional method. """
        for i in range(self.initial_hot_wall_refinement_cycles):
        
            cell_markers = fenics.MeshFunction("bool", self.mesh, self.mesh.topology().dim(), False)
            
            for cell in fenics.cells(self.mesh):
                
                found_left_boundary = False
                
                for vertex in fenics.vertices(cell):
                    
                    if fenics.near(vertex.x(0), 0.):
                        
                        found_left_boundary = True
                        
                        break
                        
                if found_left_boundary:
                    
                    cell_markers[cell] = True
            
            self.mesh = fenics.refine(self.mesh, cell_markers)
            
            
class WaterHeatDrivenCavityBenchmarkPhaseChangeSimulation(HeatDrivenCavityBenchmarkPhaseChangeSimulation):
    """ This class implements the heat-driven cavity benchmark. """
    def __init__(self):
        """ Extend the `__init__` method for the heat-driven cavity benchmark. 
        
        The tolerances set here are used during verification testing.
        """
        HeatDrivenCavityBenchmarkPhaseChangeSimulation.__init__(self)
        
        self.hot_wall_temperature_degC = 10.  # [deg C]
    
        self.cold_wall_temperature_degC = 0.  # [deg C]
        
        self.melting_temperature_degC = 0.  # [deg C]
        
        self.rayleigh_number = 2.518084e6
        
        self.prandtl_number = 6.99
        
        self.output_dir += "water/"
        
        self.adapt_timestep_to_residual = False
        
        self.quadrature_degree = 8

        self.temperature_element_degree = 2
        
        self.adaptive_goal_tolerance = 1.e-5

        self.timestep_size = 1.e-3

        self.steady_relative_tolerance = 0.1
        
        
    def do_between_timesteps(self):
        """ Keep doubling the time step size to quickly reach steady state. """
        CavityBenchmarkPhaseChangeSimulation.do_between_timesteps(self)
        
        
    def setup_derived_attributes(self):
    
        T_hot_degC = self.hot_wall_temperature_degC
    
        T_cold_degC = self.cold_wall_temperature_degC
        
        T_melt_degC = self.melting_temperature_degC
        
        def normalize_temperature(T_degC):
            """ Normalize the temperature per the scaling of the governing equations. """
            return (T_degC - T_melt_degC)/(T_hot_degC - T_cold_degC)
        

        self.normalize_temperature = normalize_temperature

        def recover_temperature_in_degrees_celsius(T):

            return T*(T_hot_degC - T_cold_degC) + T_melt_degC


        self.recover_temperature_in_degrees_celsius = recover_temperature_in_degrees_celsius


        self.hot_wall_temperature = normalize_temperature(self.hot_wall_temperature_degC)
        
        self.cold_wall_temperature = normalize_temperature(self.cold_wall_temperature_degC)
            
        self.melting_temperature = normalize_temperature(self.melting_temperature_degC)
        
        self.T_melt = fenics.Constant(self.melting_temperature)
        
        self.T_hot = fenics.Constant(self.hot_wall_temperature)
        
        self.T_cold = fenics.Constant(self.cold_wall_temperature)
        
        HeatDrivenCavityBenchmarkPhaseChangeSimulation.setup_derived_attributes(self)
        
        
    def make_buoyancy_function(self):

        T_anomaly_degC = fenics.Constant(4.0293)  # [deg C]
        
        rho_anomaly_SI = fenics.Constant(999.972)  # [kg/m^3]
        
        w = fenics.Constant(9.2793e-6)  # [(deg C)^(-q)]
        
        q = fenics.Constant(1.894816)
        
        def rho_of_T_degC(T_degC):
            """ Eq. (24) from @cite{danaila2014newton} """
            return rho_anomaly_SI*(1. - w*abs(T_degC - T_anomaly_degC)**q)
            

        def rho(T):
            """ The normalized temperature is used by Eq. (25) from @cite{danaila2014newton} """
            return rho_of_T_degC(self.recover_temperature_in_degrees_celsius(T))

        
        beta = fenics.Constant(6.91e-5) # [K^-1]
        
        T_hot_degC = fenics.Constant(self.hot_wall_temperature_degC)
    
        T_cold_degC = fenics.Constant(self.cold_wall_temperature_degC)
        
        Pr = fenics.Constant(self.prandtl_number)
        
        Ra = fenics.Constant(self.rayleigh_number)
        
        g = fenics.Constant(self.gravity)
        
        T_melt = self.T_melt
        
        def f_B(T):
            """ Eq. (25) from @cite{danaila2014newton} """
            return Ra/Pr/(beta*(T_hot_degC - T_cold_degC))*(rho(T_melt) - rho(T))/rho(T_melt)*g
        
        
        return f_B
        
        
    def verify(self):
        """ Verify against the result published in @cite{michalek2003simulations}. """
        self.verify_scalar_solution_component(
            component = 3,
            coordinates = [(x, (self.ymin + self.ymax)/2.) for x in [0.00, 0.05, 0.59, 0.80, 0.88, 1.00]],
            verified_values = [1.00, 0.66, 0.62, 0.20, 0.22, 0.00],
            relative_tolerance = 5.e-2,
            absolute_tolerance = 2.e-2)


    def setup_adaptive_goal_form(self):
        """ Set an adaptive goal based on the temperature. """
        p, u, T = fenics.split(self.state.solution)
        
        self.adaptive_goal_form = T*self.integration_metric


    def run(self, verify = True):
        """ Increment the time step size and steady tolerance to more quickly reach steady state. """
        for i in range(7):
            
            phaseflow.phasechange_simulation.PhaseChangeSimulation.run(self)
            
            self.set_timestep_size(2.*self.timestep_size)
        
            self.steady_relative_tolerance /= 2.

            self.output_dir += "continue" + str(i) + "/"


        if verify:
        
            self.verify()
