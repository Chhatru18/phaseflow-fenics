import fenics
import phaseflow


def verify_regression_water(w, mesh):
    ''' Comparing directly to the steady state benchmark data 
    from Michalek2003 in this case would take longer 
    than we should spend on a this part of the test suite. 
    So instead we subsitute this cheaper regression test.'''
    verified_solution = {'y': 0.5, 'x': [0.00, 0.10, 0.20, 0.30, 0.40, 0.70, 0.90, 1.00], 'theta': [1.000, 0.551, 0.202, 0.166, 0.211, 0.209, 0.238, 0.000]}
    
    bbt = mesh.bounding_box_tree()
    
    for i, true_theta in enumerate(verified_solution['theta']):
    
        p = fenics.Point(fenics.Point(verified_solution['x'][i], verified_solution['y']))
        
        if bbt.collides_entity(p):
            
            wval = w(p)
            
            theta = wval[3]
            
            assert(abs(theta - true_theta) < 1.e-2)

            
def wang2010_natural_convection_water(output_dir = 'output/wang2010_natural_convection_water',
    restart = False,
    restart_filepath = '',
    start_time = 0.,
    time_step_bounds = (0.001, 0.005, 0.005)):

    m = 10

    Ra = 2.518084e6
    
    Pr = 6.99
    
    T_h = 10. # [deg C]
    
    T_c = 0. # [deg C]
    
    theta_hot = 1.
    
    theta_cold = 0.
    
    T_f = T_fusion = 0. # [deg C]
    
    T_ref = T_fusion
    
    theta_f = theta_fusion = T_fusion - T_ref
    
    T_m = 4.0293 # [deg C]
        
    rho_m = 999.972 # [kg/m^3]
    
    w = 9.2793e-6 # [(deg C)^(-q)]
    
    q = 1.894816
    
    def rho(theta):            
        
        return rho_m*(1. - w*abs((T_h - T_c)*theta + T_ref - T_m)**q)
        
    def ddtheta_rho(theta):
        
        return -q*rho_m*w*abs(T_m - T_ref + theta*(T_c - T_h))**(q - 1.)*fenics.sign(T_m - T_ref + theta*(T_c - T_h))*(T_c - T_h)

    Re = phaseflow.globals.Re
    
    beta = 6.91e-5 # [K^-1]

    w, mesh = phaseflow.run(
        Ra = Ra,
        Pr = Pr,
        Ste = 1.e16,
        regularization = {'a_s': 2., 'theta_s': -1., 'R_s': 0.1},
        m_B = lambda theta : Ra/(Pr*Re*Re)/(beta*(T_h - T_c))*(rho(theta_f) - rho(theta))/rho(theta_f),
        ddtheta_m_B = lambda theta : -Ra/(Pr*Re*Re)/(beta*(T_h - T_c))*(ddtheta_rho(theta))/rho(theta_f),
        mesh = fenics.UnitSquareMesh(m, m, 'crossed'),
        time_step_bounds = time_step_bounds,
        start_time = start_time,
        end_time = 1.,
        initial_values_expression = (
            "0.",
            "0.",
            "0.",
            str(theta_hot)+"*near(x[0],  0.) + "+str(theta_cold)+"*near(x[0],  1.)"),
        boundary_conditions = [
            {'subspace': 0, 'value_expression': ("0.", "0."), 'degree': 3, 'location_expression': "near(x[0],  0.) | near(x[0],  1.) | near(x[1], 0.) | near(x[1],  1.)", 'method': "topological"},
            {'subspace': 2, 'value_expression':str(theta_hot), 'degree': 2, 'location_expression': "near(x[0],  0.)", 'method': "topological"},
            {'subspace': 2, 'value_expression':str(theta_cold), 'degree': 2, 'location_expression': "near(x[0],  1.)", 'method': "topological"}],
        restart = restart,
        restart_filepath = restart_filepath,
        output_dir = output_dir)
        
    verify_regression_water(w, mesh)


def run_wang2010_natural_convection_water():
    
    '''
    wang2010_natural_convection_water('output/wang2010_natural_convection_water_0')
    '''
    
    '''
    wang2010_natural_convection_water(restart=True,
        start_time = 0.11125,
        time_step_bounds = (0.001, 0.001, 0.005),
        output_dir='output/wang2010_natural_convection_water_1', 
        restart_filepath='output/test_regression_natural_convection_water/restart_t0.11125.hdf5')
    '''
    
    wang2010_natural_convection_water(restart=True,
        start_time = 0.25825,
        time_step_bounds = (0.001, 0.001, 0.002),
        output_dir='output/wang2010_natural_convection_water_2', 
        restart_filepath='output/wang2010_natural_convection_water_1/restart_t0.25825.hdf5')
    
if __name__=='__main__':

    run_wang2010_natural_convection_water()
